"""异步 HTTP 客户端模块"""

import asyncio
import logging
from collections.abc import Awaitable, Callable, Iterable
from urllib.parse import urlparse

import httpx
from httpx import AsyncClient, HTTPError

from aur_metadata.config import GithubConfig, HttpConfig
from aur_metadata.utils.hash import get_hash_builder

logger = logging.getLogger(__name__)

# 可重试的瞬时网络异常：建连失败/超时、读取超时、连接池超时、对端中途断开
_RETRYABLE_NETWORK_EXC: tuple[type[Exception], ...] = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.PoolTimeout,
    httpx.RemoteProtocolError,
)
# 可重试的 HTTP 状态码：限流与服务端临时故障
_RETRYABLE_STATUS: frozenset[int] = frozenset({408, 425, 429, 500, 502, 503, 504})

# 需要 GitHub 鉴权的域名：API、release 下载与 asset 重定向落点
_GITHUB_HOSTS: frozenset[str] = frozenset(
    {"api.github.com", "github.com", "objects.githubusercontent.com"}
)


def _with_github_auth(
    url: str, headers: dict[str, str], token: str | None
) -> dict[str, str]:
    """对 GitHub 域名请求注入 ``Authorization`` 头。

    token 为空则原样返回。鉴权头是叠加而非替换——在 parser 专属头或默认头基础上追加，
    不破坏「默认头与 parser 头互斥替换」的既有契约。
    """
    if not token:
        return headers
    host: str | None = urlparse(url).hostname
    if host not in _GITHUB_HOSTS:
        return headers
    merged: dict[str, str] = dict(headers)
    merged["Authorization"] = f"Bearer {token}"
    return merged


def _describe_http_error(e: HTTPError) -> str:
    """格式化 httpx 异常为「类名[: 详情]」，便于诊断网络层故障。

    网络异常（连接超时、TLS 重置、对端中断等）的 ``str(e)`` 常为空，
    仅靠 ``%s`` 打印只剩空白无法定位卡点；保留类名可区分 ConnectError /
    ConnectTimeout / ReadTimeout / RemoteProtocolError 等不同环节。
    """
    msg: str = str(e).strip()
    return f"{type(e).__name__}: {msg}" if msg else type(e).__name__


def _is_retryable(e: HTTPError) -> bool:
    """瞬时错误才重试：网络异常或可重试状态码（限流/5xx）。

    4xx（403 限流鉴权、404 不存在等）是确定性失败，重试无益且拖慢响应，
    直接放过由调用方记录并返回 None。
    """
    if isinstance(e, _RETRYABLE_NETWORK_EXC):
        return True
    return (
        isinstance(e, httpx.HTTPStatusError)
        and e.response is not None
        and e.response.status_code in _RETRYABLE_STATUS
    )


class Fetcher:
    """异步 HTTP 客户端封装。

    持有共享的 ``httpx.AsyncClient``，其生命周期由调用方（FastAPI lifespan）管理：
    构造时传入已创建的 client，应用关闭时统一 ``aclose()``。

    HTTP 行为参数（UA、超时、重试、并发、GitHub token）由 ``HttpConfig`` /
    ``GithubConfig`` 显式注入，不在模块层读全局配置。
    """

    def __init__(
        self,
        client: AsyncClient,
        http: HttpConfig,
        github: GithubConfig | None = None,
    ) -> None:
        # client 不挂默认头，按请求选择 header（原因见 _default_headers）
        self.client = client
        self._semaphore = asyncio.Semaphore(http.max_concurrent_downloads)
        # 日志中响应体截断长度（字符），避免大响应体刷屏
        self._log_body_max_length: int = http.log_body_max_length
        # 瞬时网络错误重试参数（应对国内访问上游不稳定），构造时 clamp ≥1
        self._retry_max_attempts: int = max(1, http.retry_max_attempts)
        self._retry_backoff_seconds: float = http.retry_backoff_seconds
        self._chunk_size: int = http.chunk_size
        # 可选 GitHub Token：配置后对 GitHub 域名请求统一带 Authorization，提升速率配额
        self._github_token: str | None = github.token if github else None
        # 通用默认请求头。绝大多数 parser 在没有特殊需求时直接使用这套 header。
        #
        # 重要：通用请求走 _default_headers，特殊请求走 parser.get_request_headers()——
        # 两套 header 是**互斥替换**关系，不在 httpx 客户端级别做合并。
        # 因此 Fetcher 不在 client 级别挂任何 header（避免 per-request 头被默认值
        # 污染，例如 Accept-Language 被默认值 zh-CN 替换），而是在 fetch_text 内按需
        # 二选一：传了 headers 用 parser 的，没传用默认。
        self._default_headers: dict[str, str] = {
            "User-Agent": http.user_agent,
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "max-age=0",
        }

    async def _retry[T](self, url: str, attempt: Callable[[], Awaitable[T]]) -> T:
        """对瞬时网络错误按指数退避重试，非瞬时错误或耗尽后抛出由调用方记录。

        - 瞬时错误（``_is_retryable``）：指数退避 ``backoff * 2**(n-1)`` 后重试
        - 确定性失败（4xx 等）或已达 ``retry_max_attempts``：立即/最终向上抛出

        重试只发生在网络层，hash 算法等业务错误由调用方自行捕获，不进入本方法。
        """
        last_exc: HTTPError | None = None
        for i in range(self._retry_max_attempts):
            try:
                return await attempt()
            except HTTPError as e:
                last_exc = e
                if not _is_retryable(e) or i == self._retry_max_attempts - 1:
                    raise
                wait: float = self._retry_backoff_seconds * (2**i)
                logger.warning(
                    "%s 第 %d/%d 次尝试失败：%s，%.1fs 后重试",
                    url,
                    i + 1,
                    self._retry_max_attempts,
                    _describe_http_error(e),
                    wait,
                )
                await asyncio.sleep(wait)
        # 循环正常结束意味着 max_attempts 为 0，理论不可达（构造时已 clamp ≥1）
        assert last_exc is not None
        raise last_exc

    async def fetch_text(
        self, url: str, headers: dict[str, str] | None = None
    ) -> str | None:
        """获取文本数据。

        ``headers`` 为 None 时用实例默认请求头，否则用传入集合（完整替换）。
        瞬时网络错误自动重试（见 ``_retry``）；最终失败时输出状态码 + 响应体（截断），
        便于诊断 CDN 拒绝、SNI 不匹配、403/451 等。
        """
        request_headers: dict[str, str] = _with_github_auth(
            url,
            headers if headers is not None else self._default_headers,
            self._github_token,
        )

        async def _attempt() -> str:
            response: httpx.Response = await self.client.get(
                url, headers=request_headers
            )
            response.raise_for_status()
            return response.text

        try:
            return await self._retry(url, _attempt)
        except HTTPError as e:
            logger.error("从 %s 获取文本失败: %s", url, _describe_http_error(e))
            if isinstance(e, httpx.HTTPStatusError) and e.response is not None:
                logger.error("  状态码: %d", e.response.status_code)
                body: str = e.response.text
                if body:
                    logger.error("  响应体(截断): %s", body[: self._log_body_max_length])
            return None

    async def fetch_head(
        self, url: str, max_bytes: int, headers: dict[str, str] | None = None
    ) -> bytes | None:
        """只读取响应体前 ``max_bytes`` 字节（安装包版本提取用，避免全量下载）。

        请求带 ``Range`` 头（服务端支持则只传前缀），并流式读取、凑满即主动断开，
        两道保险确保不传输剩余大文件体。瞬时网络错误自动重试（见 ``_retry``）。

        ``max_bytes`` 须为正整数。
        """
        if max_bytes <= 0:
            raise ValueError(f"max_bytes 须为正整数，得到 {max_bytes}")
        request_headers: dict[str, str] = _with_github_auth(
            url,
            headers if headers is not None else self._default_headers,
            self._github_token,
        ) | {"Range": f"bytes=0-{max_bytes - 1}"}

        async def _attempt() -> bytes:
            buffer = bytearray()
            async with self.client.stream(
                "GET", url, headers=request_headers
            ) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes(self._chunk_size):
                    buffer.extend(chunk)
                    if len(buffer) >= max_bytes:
                        break
            # 服务端可能整段返回，超出部分不参与解析，直接截掉
            return bytes(buffer[:max_bytes])

        try:
            return await self._retry(url, _attempt)
        except HTTPError as e:
            logger.error("从 %s 读取文件头部失败: %s", url, _describe_http_error(e))
            if isinstance(e, httpx.HTTPStatusError) and e.response is not None:
                logger.error("  状态码: %d", e.response.status_code)
            return None

    async def fetch_and_hash_multi(
        self,
        url: str,
        algorithms: Iterable[str],
        headers: dict[str, str] | None = None,
    ) -> dict[str, str] | None:
        """流式下载一次，同时计算多种算法的 hash，不落盘。

        多算法共享同一条下载流（逐 chunk 喂给各 builder），下载只发生一次，
        额外开销仅是多次 hash 计算（远小于下载耗时）。返回 ``{algorithm: digest}``；
        下载失败返回 None（共享流，要么全成功要么全失败）。瞬时网络错误自动重试。
        """
        request_headers: dict[str, str] = _with_github_auth(
            url,
            headers if headers is not None else self._default_headers,
            self._github_token,
        )
        algo_list: list[str] = list(algorithms)

        async def _attempt() -> dict[str, str]:
            # builder 须在每次尝试内新建，避免重试时累积上一次的部分流
            builders = {a: get_hash_builder(a)() for a in algo_list}
            async with self.client.stream(
                "GET", url, headers=request_headers
            ) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes(self._chunk_size):
                    for hash_func in builders.values():
                        hash_func.update(chunk)
            return {a: h.hexdigest() for a, h in builders.items()}

        try:
            return await self._retry(url, _attempt)
        except HTTPError as e:
            logger.error(
                "流式下载并计算 hash 失败 %s: %s", url, _describe_http_error(e)
            )
            if isinstance(e, httpx.HTTPStatusError) and e.response is not None:
                logger.error("  状态码: %d", e.response.status_code)
            return None
        except ValueError as e:
            # 算法无效是配置错误，重试无意义，直接记录
            logger.error("hash 算法无效: %s", e)
            return None

    async def fetch_and_hash_many(
        self,
        urls: dict[str, str],
        algorithms: Iterable[str],
        headers: dict[str, str] | None = None,
    ) -> dict[str, dict[str, str] | None]:
        """并发下载多个 URL，每个同时算多种算法，不落盘。

        ``urls`` 为 ``{key: url}``，返回 ``{key: {algorithm: digest} | None}``；
        某 key 下载失败则其值为 None。通过 Semaphore 限流。
        """

        async def _download_one(
            key: str, url: str
        ) -> tuple[str, dict[str, str] | None]:
            async with self._semaphore:
                result: dict[str, str] | None = await self.fetch_and_hash_multi(
                    url, algorithms, headers
                )
                return key, result

        results: list[tuple[str, dict[str, str] | None]] = await asyncio.gather(
            *[_download_one(key, url) for key, url in urls.items()]
        )
        return dict(results)
