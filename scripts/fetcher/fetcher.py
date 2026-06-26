"""HTTP 客户端模块"""

import logging

from httpx import AsyncClient, HTTPError

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.4472.124 Safari/537.36",
    "Accept": "*/*",
    "Cache-Control": "no-cache",
}


class Fetcher:
    """HTTP 客户端封装，处理网络请求"""

    def __init__(
        self, timeout: int = 10, headers: dict[str, str] | None = None
    ) -> None:
        merged_headers: dict[str, str] = DEFAULT_HEADERS.copy()
        if headers:
            merged_headers.update(headers)

        self.client = AsyncClient(timeout=timeout, headers=merged_headers)

    async def fetch_text(
        self, url: str, headers: dict[str, str] | None = None
    ) -> str | None:
        """获取文本数据"""
        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except HTTPError as e:
            logger.error("从 %s 获取文本失败: %s", url, e)
            return None
