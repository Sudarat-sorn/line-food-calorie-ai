import os
from functools import lru_cache

from app.services.food_analyzer import FoodAnalyzer
from app.services.line_client import LineClient


@lru_cache
def get_food_analyzer() -> FoodAnalyzer:
    return FoodAnalyzer()


@lru_cache
def get_line_client() -> LineClient:
    access_token = os.getenv(
        "LINE_CHANNEL_ACCESS_TOKEN"
    )

    if not access_token:
        raise RuntimeError(
            "ไม่พบ LINE_CHANNEL_ACCESS_TOKEN"
        )

    return LineClient(
        access_token=access_token
    )


def get_line_channel_secret() -> str:
    channel_secret = os.getenv(
        "LINE_CHANNEL_SECRET"
    )

    if not channel_secret:
        raise RuntimeError(
            "ไม่พบ LINE_CHANNEL_SECRET"
        )

    return channel_secret