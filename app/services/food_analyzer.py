import base64
import os

from google import genai

from app.models import FoodAnalysis


PROMPT = """
วิเคราะห์รูปอาหารนี้เป็นภาษาไทย

หน้าที่ของคุณ:
1. ระบุชื่อเมนูโดยรวม
2. แยกเฉพาะส่วนประกอบอาหารที่มองเห็น
3. ประเมินน้ำหนักแต่ละส่วนประกอบเป็นกรัม
4. ประเมินพลังงานเป็นช่วงขั้นต่ำและสูงสุด
5. ระบุ confidence ตั้งแต่ 0 ถึง 1
6. ตั้ง requires_confirmation เป็น true หากไม่แน่ใจ
7. สร้างคำถามยืนยันเพียงหนึ่งคำถามหากจำเป็น

ข้อกำหนด:
- อย่าอ้างว่าค่าพลังงานแม่นยำ 100%
- อย่าสมมติส่วนประกอบที่มองไม่เห็น
- คำนึงถึงน้ำมัน ซอส น้ำตาล และขนาดภาชนะ
- หากรูปไม่ใช่อาหาร ให้ระบุว่าไม่สามารถวิเคราะห์ได้
"""


class FoodAnalyzer:
    def __init__(
        self,
        api_key: str | None = None,
    ) -> None:
        resolved_api_key = (
            api_key or os.getenv("GEMINI_API_KEY")
        )

        if not resolved_api_key:
            raise ValueError(
                "ไม่พบ GEMINI_API_KEY"
            )

        self.client = genai.Client(
            api_key=resolved_api_key
        )

    def analyze(
        self,
        image_bytes: bytes,
        mime_type: str,
    ) -> FoodAnalysis:
        image_base64 = base64.b64encode(
            image_bytes
        ).decode("utf-8")

        interaction = self.client.interactions.create(
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
                "schema": (
                    FoodAnalysis.model_json_schema()
                ),
            },
        )

        return FoodAnalysis.model_validate_json(
            interaction.output_text
        )