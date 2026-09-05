"""HTTP 客户端模块

处理 ``aur-packages-helper`` API 的响应语义：

- 成功：HTTP 200，body ``{"code":0,"message":"ok","data":{...}}`` → 返回 body 文本
- 错误：HTTP 状态码对齐 helper 业务码前三位，body
  ``{"code":<int>,"message":<str>,"data":null}``

按状态码区分两类错误：

- **永久错误**（404 包未注册 / 422 参数错误等 4xx）：重试无意义，记日志后立即放弃
- **瞬时错误**（429 采集过频 / 5xx 上游错误·数据未就绪·内部错误，及网络异常）：
  指数退避重试，至多 ``max_retries`` 次

错误 body 的 ``message`` 一并记入日志，便于排查（如「包 'xxx' 未注册」）。
状态码语义参见 ``aur-packages-helper/app/response.py`` 的 ``ErrorCode``。
"""

import asyncio
import json
import logging
from http import HTTPStatus
from typing import Any

from httpx import AsyncClient, HTTPError

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.4472.124 Safari/537.36",
    "Accept": "*/*",
    "Cache-Control": "no-cache",
}

# 可重试的 HTTP 状态码：helper 的 429（采集过频）/ 5xx（上游错误、数据未就绪、
# 内部错误）属瞬时故障，退避后重试有望成功。其余 4xx（404 包未注册、422 参数
# 错误）为永久错误，重试无意义。
_RETRYABLE_STATUS: frozenset[int] = frozenset(
    {
        HTTPStatus.REQUEST_TIMEOUT,  # 408
        HTTPStatus.TOO_EARLY,  # 425
        HTTPStatus.TOO_MANY_REQUESTS,  # 429 helper 采集节流
        HTTPStatus.INTERNAL_SERVER_ERROR,  # 500
        HTTPStatus.BAD_GATEWAY,  # 502 helper 上游错误
        HTTPStatus.SERVICE_UNAVAILABLE,  # 503 helper 数据未就绪
        HTTPStatus.GATEWAY_TIMEOUT,  # 504
    }
)


class Fetcher:
    """HTTP 客户端封装，按 helper API 状态码语义处理请求与重试"""

    def __init__(
        self,
        timeout: int = 10,
        headers: dict[str, str] | None = None,
        max_retries: int = 3,
        retry_wait: float = 2.0,
        verify_ssl: bool = True,
    ) -> None:
        merged_headers: dict[str, str] = DEFAULT_HEADERS.copy()
        if headers:
            merged_headers.update(headers)

        if not verify_ssl:
            logger.warning("已禁用 SSL 证书校验（verify=False），仅建议在受控环境使用")
        self.client = AsyncClient(
            timeout=timeout, headers=merged_headers, verify=verify_ssl
        )
        # 瞬时错误的最大重试次数（不含首次尝试）；0 表示不重试
        self.max_retries = max_retries
        # 指数退避基数（秒）：第 n 次重试前等待 retry_wait * 2^(n-1)
        self.retry_wait = retry_wait

    async def fetch_text(
        self, url: str, headers: dict[str, str] | None = None
    ) -> str | None:
        """获取文本数据。

        - HTTP 200 → 返回 body 文本
        - 4xx 永久错误 → 记日志，返回 None（不重试）
        - 429/5xx 或网络异常 → 指数退避重试至多 ``max_retries`` 次；仍失败返回 None

        Args:
            url: 请求地址
            headers: 追加请求头（覆盖同名默认头）

        Returns:
            body 文本，或失败时 None
        """
        total_attempts = self.max_retries + 1
        last_reason: str | None = None

        for attempt in range(1, total_attempts + 1):
            try:
                response = await self.client.get(url, headers=headers)
            except HTTPError as e:
                # 网络层异常（连接超时/TLS 重置/对端中断）视为瞬时，可重试
                last_reason = f"网络错误: {e}"
                logger.warning(
                    "  请求异常（%d/%d）: %s", attempt, total_attempts, last_reason
                )
            else:
                if response.status_code == HTTPStatus.OK:
                    return response.text

                # helper 错误响应 body 含 message；提取后记入日志便于排查
                message = self._extract_message(response.text)
                last_reason = (
                    f"HTTP {response.status_code}: {message or response.reason_phrase}"
                )
                if response.status_code in _RETRYABLE_STATUS:
                    logger.warning(
                        "  可重试错误（%d/%d）: %s",
                        attempt,
                        total_attempts,
                        last_reason,
                    )
                else:
                    # 永久错误（404/422 等），重试无意义
                    logger.error("  错误: %s", last_reason)
                    return None

            # 还有重试机会则指数退避
            if attempt < total_attempts:
                backoff = self.retry_wait * (2 ** (attempt - 1))
                await asyncio.sleep(backoff)

        logger.error("  错误: 请求 %d 次均失败: %s", total_attempts, last_reason)
        return None

    @staticmethod
    def _extract_message(body: str | None) -> str | None:
        """从 helper 错误响应 body 中提取 ``message`` 字段。

        非 JSON、非对象或缺字段时返回 None，由调用方回退到 HTTP reason phrase。
        """
        if not body:
            return None
        try:
            data: Any = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            return None
        if isinstance(data, dict):
            message = data.get("message")
            if isinstance(message, str):
                return message
        return None
