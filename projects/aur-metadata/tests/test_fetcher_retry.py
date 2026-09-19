"""Fetcher 重试机制单测。

用 ``httpx.MockTransport`` 模拟瞬时网络错误与可重试状态码，验证：
- 瞬时错误后重试成功 → 返回结果
- 确定性失败（4xx）→ 立即放弃，不重试
- 重试耗尽 → 返回 None，尝试次数等于配置上限
"""

from __future__ import annotations

import httpx

from aur_metadata.config import HttpConfig
from aur_metadata.fetcher import Fetcher
from tests.fakes import make_app_config


def _make_fetcher(
    handler, max_attempts: int = 3, backoff: float = 0.0
) -> tuple[Fetcher, list[int], httpx.AsyncClient]:
    """构造带 MockTransport 的 Fetcher，重试参数经 HttpConfig 注入。"""
    calls: list[int] = [0]

    def counting_handler(request: httpx.Request) -> httpx.Response:
        calls[0] += 1
        return handler(request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(counting_handler))
    base = make_app_config().http
    http_config = HttpConfig(
        user_agent=base.user_agent,
        default_timeout=base.default_timeout,
        chunk_size=base.chunk_size,
        max_concurrent_downloads=base.max_concurrent_downloads,
        log_body_max_length=base.log_body_max_length,
        retry_max_attempts=max_attempts,
        retry_backoff_seconds=backoff,
    )
    f = Fetcher(client, http_config)
    # 关闭 client 由各测试在 finally 处理
    return f, calls, client


async def test_retry_transient_then_success() -> None:
    """首次 ConnectError，第二次成功 → 返回文本，共调用 2 次。"""
    state: list[str] = ["fail"]

    def handler(request: httpx.Request) -> httpx.Response:
        if state[0] == "fail":
            state[0] = "ok"
            raise httpx.ConnectError("网络中断")
        return httpx.Response(200, text="hello")

    f, calls, client = _make_fetcher(handler)
    try:
        result = await f.fetch_text("https://example.com/x")
        assert result == "hello"
        assert calls[0] == 2
    finally:
        await client.aclose()


async def test_no_retry_on_client_error_status() -> None:
    """404 是确定性失败，不重试，仅调用 1 次。"""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="not found")

    f, calls, client = _make_fetcher(handler)
    try:
        assert await f.fetch_text("https://example.com/x") is None
        assert calls[0] == 1
    finally:
        await client.aclose()


async def test_retry_exhausted_returns_none() -> None:
    """持续 ConnectError → 达上限后返回 None，调用次数 == max_attempts。"""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("持续失败")

    f, calls, client = _make_fetcher(handler, max_attempts=3)
    try:
        assert await f.fetch_text("https://example.com/x") is None
        assert calls[0] == 3
    finally:
        await client.aclose()


async def test_retry_on_503_then_success() -> None:
    """503 属可重试状态码，重试后成功。"""
    state: list[int] = [0]

    def handler(request: httpx.Request) -> httpx.Response:
        state[0] += 1
        if state[0] == 1:
            return httpx.Response(503, text="busy")
        return httpx.Response(200, text="ok")

    f, calls, client = _make_fetcher(handler)
    try:
        assert await f.fetch_text("https://example.com/x") == "ok"
        assert calls[0] == 2
    finally:
        await client.aclose()


async def test_retry_exhausted_on_read_timeout_stream() -> None:
    """流式下载持续 ReadTimeout → 重试至上限后返回 None。"""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("读取超时")

    f, calls, client = _make_fetcher(handler, max_attempts=2)
    try:
        assert await f.fetch_and_hash_multi("https://example.com/big", ["b2"]) is None
        assert calls[0] == 2
    finally:
        await client.aclose()
