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
from app.formatters import (
    build_food_analysis_flex,
    format_food_analysis,
)
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
    print("STEP 1: process_line_event started")

    if event.get("type") != "message":
        print("SKIP: not message event")
        return

    reply_token = event.get("replyToken")
    message = event.get("message", {})
    source = event.get("source", {})

    user_id = source.get("userId")
    source_type = source.get("type")

    print(
        "Message type:",
        message.get("type"),
    )

    if not reply_token:
        print("ERROR: reply token missing")
        return

    # ----------------------------
    # ไม่ใช่รูป
    # ----------------------------
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
        print("ERROR: message id missing")
        return

    # ----------------------------
    # Loading
    # ----------------------------
    if source_type == "user" and user_id:
        try:
            print("STEP 2: starting loading animation")

            await line_client.start_loading(
                user_id=user_id,
                loading_seconds=60,
            )

            print("STEP 2 OK: loading started")

        except Exception as error:
            print(
                "LOADING ERROR:",
                type(error).__name__,
                repr(error),
            )

    # ----------------------------
    # Download รูปจาก LINE
    # ----------------------------
    try:
        print("STEP 3: downloading LINE image")

        image_bytes, mime_type = (
            await line_client.get_message_content(
                message_id=message_id,
            )
        )

        print(
            "STEP 3 OK:",
            "bytes=",
            len(image_bytes),
            "mime=",
            mime_type,
        )

    except Exception as error:
        print(
            "IMAGE DOWNLOAD ERROR:",
            type(error).__name__,
            repr(error),
        )

        await line_client.reply_text(
            reply_token=reply_token,
            text=(
                "ขออภัย ระบบไม่สามารถดาวน์โหลดรูปจาก LINE ได้"
            ),
        )
        return

    # ----------------------------
    # ตรวจ MIME
    # ----------------------------
    if mime_type not in SUPPORTED_IMAGE_TYPES:
        print(
            "UNSUPPORTED MIME:",
            mime_type,
        )

        await line_client.reply_text(
            reply_token=reply_token,
            text=(
                f"รูปแบบไฟล์ {mime_type} ยังไม่รองรับ "
                "กรุณาส่ง JPG, PNG หรือ WEBP"
            ),
        )
        return

    # ----------------------------
    # Gemini
    # ----------------------------
    try:
        print("STEP 4: sending image to Gemini")

        analysis = await run_in_threadpool(
            analyzer.analyze,
            image_bytes,
            mime_type,
        )

        print(
            "STEP 4 OK:",
            analysis.dish_name,
        )

    except Exception as error:
        print(
            "GEMINI ERROR:",
            type(error).__name__,
            repr(error),
        )

        await line_client.reply_text(
            reply_token=reply_token,
            text=(
                "ขออภัย AI ไม่สามารถวิเคราะห์รูปอาหารได้ "
                "กรุณาลองใหม่อีกครั้ง"
            ),
        )
        return

    # ----------------------------
    # สร้าง Flex JSON
    # ----------------------------
    try:
        print("STEP 5: building Flex Message")

        flex_contents = build_food_analysis_flex(
            analysis
        )

        print("STEP 5 OK: Flex Message built")

    except Exception as error:
        print(
            "FLEX BUILD ERROR:",
            type(error).__name__,
            repr(error),
        )

        await line_client.reply_text(
            reply_token=reply_token,
            text=(
                f"{analysis.dish_name}\n"
                f"ประมาณ "
                f"{analysis.total_calories_min:.0f}-"
                f"{analysis.total_calories_max:.0f} kcal\n\n"
                "วิเคราะห์สำเร็จ แต่สร้างการ์ด Flex ไม่สำเร็จ"
            ),
        )
        return

    # ----------------------------
    # ส่ง Flex
    # ----------------------------
    alt_text = (
        f"{analysis.dish_name}: "
        f"{analysis.total_calories_min:.0f}-"
        f"{analysis.total_calories_max:.0f} kcal"
    )

    try:
        print("STEP 6: sending Flex Message")

        await line_client.reply_flex(
            reply_token=reply_token,
            alt_text=alt_text,
            contents=flex_contents,
        )

        print("STEP 6 OK: Flex Message sent")

    except Exception as error:
        print(
            "FLEX SEND ERROR:",
            type(error).__name__,
            repr(error),
        )
        
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
   