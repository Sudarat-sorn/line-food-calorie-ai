import os
import sys

from dotenv import load_dotenv
from google import genai


def main() -> None:
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("ERROR: ไม่พบ GEMINI_API_KEY ในไฟล์ .env")
        sys.exit(1)

    try:
        client = genai.Client(api_key=api_key)

        interaction = client.interactions.create(
            model="gemini-3.5-flash-lite",
            input=(
                "ตอบเป็นภาษาไทยว่า Gemini API พร้อมใช้งานแล้ว "
                "โดยตอบไม่เกินหนึ่งประโยค"
            ),
        )

        print("Gemini response:")
        print(interaction.output_text)

    except Exception as error:
        print(f"ERROR: เรียก Gemini API ไม่สำเร็จ: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()