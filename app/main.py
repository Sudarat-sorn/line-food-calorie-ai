import json
from typing import Annotated

from dotenv import load_dotenv
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    Header,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.concurrency import run_in_threadpool

from app.dependencies import (
    get_food_analyzer,
    get_line_channel_secret,
    get_line_client,
)
from app.formatters import format_food_analysis
from app.models import FoodAnalysis
from app.security import verify_line_signature
from app.services.food_analyzer import FoodAnalyzer
from app.services.line_client import LineClient

load_dotenv()

app = FastAPI(
    title="LINE Food Calorie AI",
    version="0.1.0",
)

SUPPORTED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/analyze",
    response_model=FoodAnalysis,
)
async def analyze_food(
    file: Annotated[
        UploadFile,
        File(description="รูปอาหาร"),
    ],
    analyzer: Annotated[
        FoodAnalyzer,
        Depends(get_food_analyzer),
    ],
) -> FoodAnalysis:
    content_type = file.content_type

    if content_type not in SUPPORTED_IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=(
                "รองรับเฉพาะไฟล์ JPG, PNG และ WEBP"
            ),
        )

    image_bytes = await file.read()
    await file.close()

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="ไฟล์รูปว่างเปล่า",
        )

    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="ไฟล์รูปต้องมีขนาดไม่เกิน 10 MB",
        )

    try:
        result = await run_in_threadpool(
            analyzer.analyze,
            image_bytes,
            content_type,
        )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        print(f"Gemini API error: {error}")

        raise HTTPException(
            status_code=502,
            detail="ไม่สามารถวิเคราะห์รูปอาหารได้",
        ) from error

async def process_line_event(
    event: dict,
    analyzer: FoodAnalyzer,
    line_client: LineClient,
) -> None:
    if event.get("type") != "message":
        return

    reply_token = event.get("replyToken")
    message = event.get("message", {})

    if not reply_token:
        return

    if message.get("type") != "image":
        await line_client.reply_text(
            reply_token=reply_token,
            text=(
                "กรุณาส่งรูปอาหารหนึ่งจาน "
                "เพื่อให้ AI ประเมินแคลอรีครับ 🍽"
            ),
        )
        return

    message_id = message.get("id")

    if not message_id:
        return

    try:
        image_bytes, mime_type = (
            await line_client.get_message_content(
                message_id=message_id,
            )
        )

        if mime_type not in SUPPORTED_IMAGE_TYPES:
            await line_client.reply_text(
                reply_token=reply_token,
                text=(
                    "รูปแบบไฟล์นี้ยังไม่รองรับ "
                    "กรุณาส่งรูป JPG, PNG หรือ WEBP"
                ),
            )
            return

        analysis = await run_in_threadpool(
            analyzer.analyze,
            image_bytes,
            mime_type,
        )

        reply_message = format_food_analysis(
            analysis
        )

    except Exception as error:
        print(f"LINE image analysis error: {error}")

        reply_message = (
            "ขออภัย ไม่สามารถวิเคราะห์รูปนี้ได้ "
            "กรุณาลองส่งรูปอาหารที่ชัดเจนอีกครั้ง"
        )

    try:
        await line_client.reply_text(
            reply_token=reply_token,
            text=reply_message,
        )
    except Exception as error:
        print(f"LINE reply error: {error}")

@app.post("/webhook")
async def line_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    analyzer: Annotated[
        FoodAnalyzer,
        Depends(get_food_analyzer),
    ],
    line_client: Annotated[
        LineClient,
        Depends(get_line_client),
    ],
    channel_secret: Annotated[
        str,
        Depends(get_line_channel_secret),
    ],
    x_line_signature: Annotated[
        str | None,
        Header(alias="X-Line-Signature"),
    ] = None,
) -> dict[str, str]:
    raw_body = await request.body()

    if not x_line_signature:
        raise HTTPException(
            status_code=400,
            detail="ไม่พบ X-Line-Signature",
        )

    if not verify_line_signature(
        body=raw_body,
        signature=x_line_signature,
        channel_secret=channel_secret,
    ):
        raise HTTPException(
            status_code=400,
            detail="LINE Signature ไม่ถูกต้อง",
        )

    try:
        payload = json.loads(
            raw_body.decode("utf-8")
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as error:
        raise HTTPException(
            status_code=400,
            detail="Webhook body ไม่ถูกต้อง",
        ) from error

    for event in payload.get("events", []):
        background_tasks.add_task(
            process_line_event,
            event,
            analyzer,
            line_client,
        )

    return {"status": "ok"}
   