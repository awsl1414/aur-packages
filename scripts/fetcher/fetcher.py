from typing import Any
from httpx import AsyncClient


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.4472.124 Safari/537.36",
    "Accept": "*/*",
    "Cache-Control": "no-cache",
}


class Fetcher:
    """
    负责底层 HTTP 请求，不关心版本号解析，也不关心包来源。
    """

    def __init__(
        self, timeout: int = 10, headers: dict[str, str] | None = None
    ) -> None:
        merged_headers = DEFAULT_HEADERS.copy()
        if headers:
            merged_headers.update(headers)

        self.client = AsyncClient(timeout=timeout, headers=merged_headers)

    async def fetch_json(
        self, url: str, headers: dict[str, str] | None = None
    ) -> Any | None:
        """
        请求 URL 返回 JSON 数据
        """
        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"从 {url} 获取 JSON 失败: {e}")
            return None

    async def fetch_text(
        self, url: str, headers: dict[str, str] | None = None
    ) -> str | None:
        """
        请求 URL 返回文本数据
        """
        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"从 {url} 获取文本失败: {e}")
            return None
