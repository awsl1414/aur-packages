"""Fetcher.fetch_head 单测：Range 头、流式截断与重试语义。"""

from __future__ import annotations

import httpx
import pytest

from aur_metadata.config import HttpConfig
from aur_metadata.fetcher import Fetcher
from tests.fakes import make_app_config


def _make_fetcher(
    handler, max_attempts: int = 2
) -> tuple[Fetcher, list[int]]:
    """构造带 MockTransport 的 Fetcher：零退避，尝试次数可调（经 HttpConfig 注入）"""
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
        retry_backoff_seconds=0.0,
    )
    f = Fetcher(client, http_config)
    return f, calls


async def test_fetch_head_reads_prefix_and_sends_range() -> None:
    """只返回前 max_bytes 字节，且请求携带 Range 头"""
    seen_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.update(request.headers)
        return httpx.Response(200, content=bytes(range(256)) * 8)  # 2048 字节

    f, calls = _make_fetcher(handler)
    result = await f.fetch_head("https://x/big.deb", 256)
    assert result == bytes(range(256))
    assert seen_headers["range"] == "bytes=0-255"
    assert calls[0] == 1


async def test_fetch_head_short_body_returns_all() -> None:
    """响应体不足 max_bytes → 原样返回全部"""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"small")

    f, _ = _make_fetcher(handler)
    assert await f.fetch_head("https://x/small.deb", 1024) == b"small"


async def test_fetch_head_retry_transient_then_success() -> None:
    state: list[str] = ["fail"]

    def handler(request: httpx.Request) -> httpx.Response:
        if state[0] == "fail":
            state[0] = "ok"
            raise httpx.ConnectError("网络中断")
        return httpx.Response(200, content=b"head-data")

    f, calls = _make_fetcher(handler)
    assert await f.fetch_head("https://x/a.deb", 64) == b"head-data"
    assert calls[0] == 2


async def test_fetch_head_404_returns_none() -> None:
    """404 确定性失败不重试，返回 None"""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="not found")

    f, calls = _make_fetcher(handler)
    assert await f.fetch_head("https://x/missing.deb", 64) is None
    assert calls[0] == 1


async def test_fetch_head_invalid_max_bytes_raises() -> None:
    f, _ = _make_fetcher(lambda request: httpx.Response(200, content=b"x"))
    with pytest.raises(ValueError):
        await f.fetch_head("https://x/a.deb", 0)
