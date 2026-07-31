import httpx


LINE_API_BASE_URL = "https://api.line.me"
LINE_DATA_API_BASE_URL = "https://api-data.line.me"


class LineClient:
    def __init__(
        self,
        access_token: str,
    ) -> None:
        self.headers = {
            "Authorization": f"Bearer {access_token}",
        }

    async def get_message_content(
        self,
        message_id: str,
    ) -> tuple[bytes, str]:
        url = (
            f"{LINE_DATA_API_BASE_URL}"
            f"/v2/bot/message/{message_id}/content"
        )

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:
            response = await client.get(
                url,
                headers=self.headers,
            )
            response.raise_for_status()

        content_type = response.headers.get(
            "content-type",
            "image/jpeg",
        )
        content_type = content_type.split(";")[0].strip()

        return response.content, content_type

    async def reply_text(
        self,
        reply_token: str,
        text: str,
    ) -> None:
        url = (
            f"{LINE_API_BASE_URL}"
            "/v2/bot/message/reply"
        )

        payload = {
            "replyToken": reply_token,
            "messages": [
                {
                    "type": "text",
                    "text": text,
                }
            ],
        }

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:
            response = await client.post(
                url,
                headers={
                    **self.headers,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()