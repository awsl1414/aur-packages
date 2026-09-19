"""Fetcher.fetch_head 单测：Range 头、流式截断与重试语义。"""

from __future__ import annotations

import httpx
import pytest

from app import fetcher as fetcher_module
from app.fetcher import Fetcher


def _make_fetcher(
    handler, monkeypatch: pytest.MonkeyPatch, max_attempts: int = 3
) -> tuple[Fetcher, list[int]]:
    calls: list[int] = [0]

    def counting_handler(request: httpx.Request) -> httpx.Response:
        calls[0] += 1
        return handler(request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(counting_handler))
    f = Fetcher(client)
    # monkey 夹具自动还原，模块级重试常量不泄漏到其他测试
    monkeypatch.setattr(fetcher_module, "_RETRY_MAX_ATTEMPTS", max_attempts)
    monkeypatch.setattr(fetcher_module, "_RETRY_BACKOFF_SECONDS", 0.0)
    return f, calls


async def test_fetch_head_reads_prefix_and_sends_range(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """只返回前 max_bytes 字节，且请求携带 Range 头"""
    seen_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.update(request.headers)
        return httpx.Response(200, content=bytes(range(256)) * 8)  # 2048 字节

    f, calls = _make_fetcher(handler, monkeypatch)
    result = await f.fetch_head("https://x/big.deb", 256)
    assert result == bytes(range(256))
    assert seen_headers["range"] == "bytes=0-255"
    assert calls[0] == 1


async def test_fetch_head_short_body_returns_all(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """响应体不足 max_bytes → 原样返回全部"""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"small")

    f, _ = _make_fetcher(handler, monkeypatch)
    assert await f.fetch_head("https://x/small.deb", 1024) == b"small"


async def test_fetch_head_retry_transient_then_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state: list[str] = ["fail"]

    def handler(request: httpx.Request) -> httpx.Response:
        if state[0] == "fail":
            state[0] = "ok"
            raise httpx.ConnectError("网络中断")
        return httpx.Response(200, content=b"head-data")

    f, calls = _make_fetcher(handler, monkeypatch)
    assert await f.fetch_head("https://x/a.deb", 64) == b"head-data"
    assert calls[0] == 2


async def test_fetch_head_404_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """404 确定性失败不重试，返回 None"""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="not found")

    f, calls = _make_fetcher(handler, monkeypatch)
    assert await f.fetch_head("https://x/missing.deb", 64) is None
    assert calls[0] == 1


async def test_fetch_head_invalid_max_bytes_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    f, _ = _make_fetcher(lambda request: httpx.Response(200, content=b"x"), monkeypatch)
    with pytest.raises(ValueError):
        await f.fetch_head("https://x/a.deb", 0)
