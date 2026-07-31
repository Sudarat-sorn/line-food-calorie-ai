import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_food_analyzer
from app.main import app
from app.models import FoodAnalysis, FoodItem


class FakeFoodAnalyzer:
    def analyze(
        self,
        image_bytes: bytes,
        mime_type: str,
    ) -> FoodAnalysis:
        return FoodAnalysis(
            dish_name="ส้มตำไทย",
            items=[
                FoodItem(
                    name="มะละกอดิบขูด",
                    estimated_grams=120,
                    calories_min=15,
                    calories_max=20,
                    confidence=0.95,
                )
            ],
            total_calories_min=15,
            total_calories_max=20,
            confidence=0.90,
            requires_confirmation=True,
            confirmation_question="ใส่น้ำตาลมากหรือไม่",
            notes=[
                "ค่าพลังงานขึ้นอยู่กับปริมาณเครื่องปรุง"
            ],
        )


@pytest.fixture
def client() -> TestClient:
    app.dependency_overrides[get_food_analyzer] = (
        lambda: FakeFoodAnalyzer()
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_health_returns_ok(
    client: TestClient,
) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_food_image(
    client: TestClient,
) -> None:
    response = client.post(
        "/analyze",
        files={
            "file": (
                "food.jpg",
                b"fake-image-content",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["dish_name"] == "ส้มตำไทย"
    assert result["total_calories_min"] == 15
    assert result["total_calories_max"] == 20
    assert result["requires_confirmation"] is True


def test_rejects_non_image_file(
    client: TestClient,
) -> None:
    response = client.post(
        "/analyze",
        files={
            "file": (
                "document.txt",
                b"not-an-image",
                "text/plain",
            )
        },
    )

    assert response.status_code == 415
    assert response.json()["detail"] == (
        "รองรับเฉพาะไฟล์ JPG, PNG และ WEBP"
    )