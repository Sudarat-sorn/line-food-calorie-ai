from pydantic import BaseModel, Field


class FoodItem(BaseModel):
    name: str = Field(
        description="ชื่ออาหารหรือส่วนประกอบภาษาไทย"
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
        description="ค่าความมั่นใจตั้งแต่ 0 ถึง 1",
    )


class FoodAnalysis(BaseModel):
    dish_name: str
    items: list[FoodItem]
    total_calories_min: float = Field(ge=0)
    total_calories_max: float = Field(ge=0)
    confidence: float = Field(ge=0, le=1)
    requires_confirmation: bool
    confirmation_question: str | None = None
    notes: list[str]