from app.models import FoodAnalysis


def format_food_analysis(
    result: FoodAnalysis,
) -> str:
    lines = [
        f"🍽 เมนู: {result.dish_name}",
        "",
        "ส่วนประกอบที่ตรวจพบ:",
    ]

    for item in result.items:
        lines.append(
            f"• {item.name}: "
            f"ประมาณ {item.estimated_grams:.0f} กรัม "
            f"({item.calories_min:.0f}-"
            f"{item.calories_max:.0f} kcal)"
        )

    confidence_percent = round(
        result.confidence * 100
    )

    lines.extend(
        [
            "",
            "🔥 พลังงานรวมโดยประมาณ",
            (
                f"{result.total_calories_min:.0f}-"
                f"{result.total_calories_max:.0f} kcal"
            ),
            "",
            f"ความมั่นใจ: {confidence_percent}%",
        ]
    )

    if result.confirmation_question:
        lines.extend(
            [
                "",
                "❓ คำถามเพิ่มเติม",
                result.confirmation_question,
            ]
        )

    if result.notes:
        lines.extend(
            [
                "",
                "หมายเหตุ:",
            ]
        )

        for note in result.notes:
            lines.append(f"• {note}")

    lines.extend(
        [
            "",
            "ผลลัพธ์นี้เป็นเพียงค่าประมาณจากรูปภาพ",
        ]
    )

    return "\n".join(lines)