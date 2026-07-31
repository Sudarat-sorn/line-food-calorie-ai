import base64
import mimetypes
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field


class FoodItem(BaseModel):
    name: str = Field(
        description="ชื่ออาหารหรือส่วนประกอบที่มองเห็น เป็นภาษาไทย"
    )
    estimated_grams: float = Field(
        ge=0,
        description="น้ำหนักโดยประมาณ หน่วยกรัม",
    )
    calories_min: float = Field(
        ge=0,
        description="พลังงานขั้นต่ำโดยประมาณ",
    )
    calories_max: float = Field(
        ge=0,
        description="พลังงานสูงสุดโดยประมาณ",
    )
    confidence: float = Field(
        ge=0,
        le=1,
        description="ความมั่นใจในการจำแนก ตั้งแต่ 0 ถึง 1",
    )


class FoodAnalysis(BaseModel):
    dish_name: str = Field(
        description="ชื่อเมนูโดยรวม เป็นภาษาไทย"
    )
    items: list[FoodItem] = Field(
        description="รายการอาหารหรือส่วนประกอบที่มองเห็น"
    )
    total_calories_min: float = Field(
        ge=0,
        description="พลังงานรวมขั้นต่ำโดยประมาณ",
    )
    total_calories_max: float = Field(
        ge=0,
        description="พลังงานรวมสูงสุดโดยประมาณ",
    )
    confidence: float = Field(
        ge=0,
        le=1,
        description="ความมั่นใจโดยรวม ตั้งแต่ 0 ถึง 1",
    )
    requires_confirmation: bool = Field(
        description="ต้องถามผู้ใช้เพิ่มเติมหรือไม่"
    )
    confirmation_question: str | None = Field(
        default=None,
        description="คำถามสั้น ๆ สำหรับยืนยันปริมาณอาหาร",
    )
    notes: list[str] = Field(
        description="ข้อสังเกตหรือสาเหตุที่ทำให้ค่าคลาดเคลื่อน"
    )


PROMPT = """
วิเคราะห์รูปอาหารนี้เป็นภาษาไทย

หน้าที่ของคุณ:
1. ระบุชื่อเมนูโดยรวม
2. แยกเฉพาะส่วนประกอบอาหารที่มองเห็น
3. ประเมินน้ำหนักของแต่ละส่วนประกอบเป็นกรัม
4. ประเมินพลังงานเป็นช่วงขั้นต่ำและสูงสุด
5. ระบุ confidence ตั้งแต่ 0 ถึง 1
6. ตั้ง requires_confirmation เป็น true หากไม่แน่ใจเรื่องปริมาณ
7. สร้างคำถามยืนยันเพียงหนึ่งคำถามหากจำเป็น

ข้อกำหนด:
- อย่าอ้างว่าค่าพลังงานแม่นยำ 100%
- อย่าสมมติส่วนประกอบที่มองไม่เห็น
- คำนึงถึงความไม่แน่นอนของน้ำมัน ซอส น้ำตาล และขนาดจาน
- หากรูปไม่ใช่อาหาร ให้ระบุว่าไม่สามารถวิเคราะห์ได้อย่างชัดเจน
"""


def encode_image(image_path: Path) -> tuple[str, str]:
    mime_type, _ = mimetypes.guess_type(image_path.name)

    supported_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    if mime_type not in supported_types:
        raise ValueError(
            "รองรับเฉพาะไฟล์ JPG, JPEG, PNG และ WEBP"
        )

    image_bytes = image_path.read_bytes()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    return image_base64, mime_type


def main() -> None:
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("ERROR: ไม่พบ GEMINI_API_KEY ในไฟล์ .env")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("วิธีใช้: python test_food_image.py food.jpg")
        sys.exit(1)

    image_path = Path(sys.argv[1])

    if not image_path.is_file():
        print(f"ERROR: ไม่พบไฟล์รูป {image_path}")
        sys.exit(1)

    try:
        image_base64, mime_type = encode_image(image_path)

        client = genai.Client(api_key=api_key)

        interaction = client.interactions.create(
            model="gemini-3.5-flash-lite",
            store=False,
            input=[
                {
                    "type": "text",
                    "text": PROMPT,
                },
                {
                    "type": "image",
                    "data": image_base64,
                    "mime_type": mime_type,
                },
            ],
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": FoodAnalysis.model_json_schema(),
            },
        )

        result = FoodAnalysis.model_validate_json(
            interaction.output_text
        )

        print("=== ผลการวิเคราะห์อาหาร ===")
        print(result.model_dump_json(indent=2))

    except Exception as error:
        print(f"ERROR: วิเคราะห์รูปไม่สำเร็จ: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()