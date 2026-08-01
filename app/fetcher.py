"""异步 HTTP 客户端模块"""

import asyncio
import logging
from urllib.parse import urlparse

import httpx
from httpx import AsyncClient, HTTPError

from app.config import config
from app.constants import (
    CHUNK_SIZE,
    MAX_CONCURRENT_DOWNLOADS,
    USER_AGENT,
    HashAlgorithmEnum,
)
from app.utils.hash import get_hash_builder

logger = logging.getLogger(__name__)

# 日志中响应体截断长度（字符），避免大响应体刷屏
_LOG_BODY_MAX_LENGTH: int = config.http.log_body_max_length

# 可选 GitHub Token：配置后对 GitHub 域名请求统一带 Authorization，提升速率配额
_GITHUB_TOKEN: str | None = config.github.token

# 需要 GitHub 鉴权的域名：API、release 下载与 asset 重定向落点
_GITHUB_HOSTS: frozenset[str] = frozenset(
    {"api.github.com", "github.com", "objects.githubusercontent.com"}
)

# 通用默认请求头。绝大多数 parser 在没有特殊需求时直接使用这套 header。
#
# 重要：通用请求走 DEFAULT_HEADERS，特殊请求走 parser.get_request_headers()——
# 两套 header 是**互斥替换**关系，不在 httpx 客户端级别做合并。
# 因此 Fetcher 不在 client 级别挂任何 header（避免 per-request 头被默认值
# 污染，例如 Accept-Language 被默认值 zh-CN 替换），而是在 fetch_text 内按需
# 二选一：传了 headers 用 parser 的，没传用默认。
DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": USER_AGENT,
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "max-age=0",
}


def _with_github_auth(url: str, headers: dict[str, str]) -> dict[str, str]:
    """对 GitHub 域名请求注入 ``Authorization`` 头。

    token 为空则原样返回。鉴权头是叠加而非替换——在 parser 专属头或默认头基础上追加，
    不破坏「默认头与 parser 头互斥替换」的既有契约。
    """
    if not _GITHUB_TOKEN:
        return headers
    host: str | None = urlparse(url).hostname
    if host not in _GITHUB_HOSTS:
        return headers
    merged: dict[str, str] = dict(headers)
    merged["Authorization"] = f"Bearer {_GITHUB_TOKEN}"
    return merged


class Fetcher:
    """异步 HTTP 客户端封装。

    持有共享的 ``httpx.AsyncClient``，其生命周期由调用方（FastAPI lifespan）管理：
    构造时传入已创建的 client，应用关闭时统一 ``aclose()``。
    """

    def __init__(
        self, client: AsyncClient, max_concurrent: int = MAX_CONCURRENT_DOWNLOADS
    ) -> None:
        # client 不挂默认头，按请求选择 header（原因见 DEFAULT_HEADERS）
        self.client = client
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_text(
        self, url: str, headers: dict[str, str] | None = None
    ) -> str | None:
        """获取文本数据。

        ``headers`` 为 None 时用 ``DEFAULT_HEADERS``，否则用传入集合（完整替换）。
        失败时输出状态码 + 响应体（截断），便于诊断 CDN 拒绝、SNI 不匹配、403/451 等。
        """
        request_headers: dict[str, str] = _with_github_auth(
            url, headers if headers is not None else DEFAULT_HEADERS
        )
        try:
            response = await self.client.get(url, headers=request_headers)
            response.raise_for_status()
            return response.text
        except HTTPError as e:
            logger.error("从 %s 获取文本失败: %s", url, e)
            if isinstance(e, httpx.HTTPStatusError) and e.response is not None:
                logger.error("  状态码: %d", e.response.status_code)
                body: str = e.response.text
                if body:
                    logger.error("  响应体(截断): %s", body[:_LOG_BODY_MAX_LENGTH])
            return None

    async def fetch_and_hash(
        self,
        url: str,
        algorithm: str = HashAlgorithmEnum.B2.value,
        headers: dict[str, str] | None = None,
    ) -> str | None:
        """流式下载 URL 内容并边下边算 hash，不落盘。

        用于计算文件 hash 而无需在本地保存完整文件。``headers`` 为 None 时
        使用 ``DEFAULT_HEADERS``。失败时返回 None 并记日志。
        """
        request_headers: dict[str, str] = _with_github_auth(
            url, headers if headers is not None else DEFAULT_HEADERS
        )
        try:
            builder = get_hash_builder(algorithm)
            hash_func = builder()
            async with self.client.stream(
                "GET", url, headers=request_headers
            ) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes(CHUNK_SIZE):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except HTTPError as e:
            logger.error("流式下载并计算 hash 失败 %s: %s", url, e)
            if isinstance(e, httpx.HTTPStatusError) and e.response is not None:
                logger.error("  状态码: %d", e.response.status_code)
            return None
        except ValueError as e:
            logger.error("hash 算法无效: %s", e)
            return None

    async def fetch_and_hash_many(
        self,
        urls: dict[str, str],
        algorithm: str = HashAlgorithmEnum.B2.value,
        headers: dict[str, str] | None = None,
    ) -> dict[str, str | None]:
        """并发下载多个 URL 并计算 hash，不落盘。

        ``urls`` 为 ``{key: url}`` 映射，返回 ``{key: hash | None}``。
        每个下载通过 Semaphore 限流，失败的 key 记 None。
        """

        async def _download_one(key: str, url: str) -> tuple[str, str | None]:
            async with self._semaphore:
                digest: str | None = await self.fetch_and_hash(url, algorithm, headers)
                return key, digest

        results: list[tuple[str, str | None]] = await asyncio.gather(
            *[_download_one(key, url) for key, url in urls.items()]
        )
        return dict(results)
