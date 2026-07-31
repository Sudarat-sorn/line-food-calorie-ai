from app.formatters import build_food_analysis_flex
from app.models import FoodAnalysis, FoodItem


def collect_texts(value: object) -> list[str]:
    texts: list[str] = []

    if isinstance(value, dict):
        if (
            value.get("type") == "text"
            and isinstance(value.get("text"), str)
        ):
            texts.append(value["text"])

        for child in value.values():
            texts.extend(collect_texts(child))

    elif isinstance(value, list):
        for child in value:
            texts.extend(collect_texts(child))

    return texts


def test_build_food_analysis_flex() -> None:
    analysis = FoodAnalysis(
        dish_name="ส้มตำไทย",
        items=[
            FoodItem(
                name="มะละกอดิบขูด",
                estimated_grams=120,
                calories_min=15,
                calories_max=20,
                confidence=0.95,
            ),
            FoodItem(
                name="ถั่วลิสงคั่ว",
                estimated_grams=25,
                calories_min=140,
                calories_max=160,
                confidence=0.90,
            ),
        ],
        total_calories_min=255,
        total_calories_max=350,
        confidence=0.88,
        requires_confirmation=True,
        confirmation_question=(
            "จานนี้ใส่น้ำตาลในปริมาณมากหรือไม่?"
        ),
        notes=[
            "ปริมาณน้ำตาลมีผลต่อพลังงานรวม",
        ],
    )

    flex = build_food_analysis_flex(analysis)
    texts = collect_texts(flex)

    assert flex["type"] == "bubble"
    assert "ส้มตำไทย" in texts
    assert "255-350" in texts
    assert "88%" in texts
    assert "มะละกอดิบขูด" in texts
    assert "ถั่วลิสงคั่ว" in texts