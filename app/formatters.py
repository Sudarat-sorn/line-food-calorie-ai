from typing import Any

from app.models import FoodAnalysis, FoodItem


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


def _build_food_item_row(
    item: FoodItem,
) -> dict[str, Any]:
    return {
        "type": "box",
        "layout": "horizontal",
        "spacing": "md",
        "margin": "md",
        "contents": [
            {
                "type": "box",
                "layout": "vertical",
                "flex": 5,
                "contents": [
                    {
                        "type": "text",
                        "text": item.name,
                        "size": "sm",
                        "weight": "bold",
                        "color": "#1F2937",
                        "wrap": True,
                    },
                    {
                        "type": "text",
                        "text": (
                            f"ประมาณ "
                            f"{item.estimated_grams:.0f} กรัม"
                        ),
                        "size": "xs",
                        "color": "#6B7280",
                        "margin": "xs",
                        "wrap": True,
                    },
                ],
            },
            {
                "type": "text",
                "text": (
                    f"{item.calories_min:.0f}-"
                    f"{item.calories_max:.0f} kcal"
                ),
                "size": "sm",
                "weight": "bold",
                "color": "#F97316",
                "align": "end",
                "gravity": "center",
                "flex": 3,
                "wrap": True,
            },
        ],
    }


def build_food_analysis_flex(
    result: FoodAnalysis,
) -> dict[str, Any]:
    displayed_items = result.items[:6]

    hidden_item_count = max(
        len(result.items) - len(displayed_items),
        0,
    )

    item_contents: list[dict[str, Any]] = []

    if displayed_items:
        for item in displayed_items:
            item_contents.append(
                _build_food_item_row(item)
            )
    else:
        item_contents.append(
            {
                "type": "text",
                "text": "ไม่พบส่วนประกอบที่ระบุได้",
                "size": "sm",
                "color": "#6B7280",
                "wrap": True,
                "margin": "md",
            }
        )

    if hidden_item_count > 0:
        item_contents.append(
            {
                "type": "text",
                "text": (
                    f"และอีก {hidden_item_count} รายการ"
                ),
                "size": "xs",
                "color": "#6B7280",
                "align": "center",
                "margin": "md",
            }
        )

    confidence_percent = round(
        result.confidence * 100
    )

    body_contents: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": "พลังงานโดยประมาณ",
            "size": "sm",
            "color": "#6B7280",
        },
        {
            "type": "box",
            "layout": "horizontal",
            "margin": "sm",
            "contents": [
                {
                    "type": "text",
                    "text": (
                        f"{result.total_calories_min:.0f}-"
                        f"{result.total_calories_max:.0f}"
                    ),
                    "size": "3xl",
                    "weight": "bold",
                    "color": "#F97316",
                    "flex": 0,
                },
                {
                    "type": "text",
                    "text": "kcal",
                    "size": "md",
                    "weight": "bold",
                    "color": "#F97316",
                    "gravity": "bottom",
                    "margin": "sm",
                    "flex": 0,
                },
            ],
        },
        {
            "type": "box",
            "layout": "horizontal",
            "margin": "md",
            "paddingAll": "10px",
            "backgroundColor": "#ECFDF5",
            "cornerRadius": "md",
            "contents": [
                {
                    "type": "text",
                    "text": "ความมั่นใจของ AI",
                    "size": "sm",
                    "color": "#047857",
                    "flex": 1,
                },
                {
                    "type": "text",
                    "text": f"{confidence_percent}%",
                    "size": "sm",
                    "weight": "bold",
                    "color": "#047857",
                    "align": "end",
                    "flex": 0,
                },
            ],
        },
        {
            "type": "separator",
            "margin": "lg",
            "color": "#E5E7EB",
        },
        {
            "type": "text",
            "text": "ส่วนประกอบที่ตรวจพบ",
            "size": "md",
            "weight": "bold",
            "color": "#111827",
            "margin": "lg",
        },
        *item_contents,
    ]

    if result.confirmation_question:
        body_contents.extend(
            [
                {
                    "type": "separator",
                    "margin": "lg",
                    "color": "#E5E7EB",
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "lg",
                    "paddingAll": "12px",
                    "backgroundColor": "#FFF7ED",
                    "cornerRadius": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": "คำถามเพิ่มเติม",
                            "size": "xs",
                            "weight": "bold",
                            "color": "#C2410C",
                        },
                        {
                            "type": "text",
                            "text": (
                                result.confirmation_question
                            ),
                            "size": "sm",
                            "color": "#7C2D12",
                            "wrap": True,
                            "margin": "sm",
                        },
                    ],
                },
            ]
        )

    if result.notes:
        note_text = "\n".join(
            f"• {note}"
            for note in result.notes[:2]
        )

        body_contents.extend(
            [
                {
                    "type": "text",
                    "text": "หมายเหตุ",
                    "size": "xs",
                    "weight": "bold",
                    "color": "#6B7280",
                    "margin": "lg",
                },
                {
                    "type": "text",
                    "text": note_text,
                    "size": "xs",
                    "color": "#6B7280",
                    "wrap": True,
                    "margin": "sm",
                },
            ]
        )

    return {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "20px",
            "backgroundColor": "#0F766E",
            "contents": [
                {
                    "type": "text",
                    "text": "AI FOOD ANALYSIS",
                    "size": "xs",
                    "weight": "bold",
                    "color": "#CCFBF1",
                },
                {
                    "type": "text",
                    "text": result.dish_name,
                    "size": "xl",
                    "weight": "bold",
                    "color": "#FFFFFF",
                    "wrap": True,
                    "margin": "sm",
                },
            ],
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "20px",
            "contents": body_contents,
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "14px",
            "backgroundColor": "#F9FAFB",
            "contents": [
                {
                    "type": "text",
                    "text": (
                        "ค่าพลังงานเป็นการประเมินจากรูปภาพ "
                        "ไม่ใช่คำแนะนำทางการแพทย์"
                    ),
                    "size": "xxs",
                    "color": "#9CA3AF",
                    "wrap": True,
                    "align": "center",
                }
            ],
        },
        "styles": {
            "header": {
                "separator": False,
            },
            "footer": {
                "separator": True,
                "separatorColor": "#E5E7EB",
            },
        },
    }