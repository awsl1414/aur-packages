from unittest.mock import AsyncMock, patch

import httpx
import pytest

from fetcher.fetcher import Fetcher

URL = "https://aur.llz.asia/api/v1/packages/qq?algorithm=b2"


def _response(status_code: int, text: str = "") -> httpx.Response:
    """构造一个真实 httpx.Response，便于 status_code/reason_phrase/text 都可用"""
    return httpx.Response(
        status_code=status_code, text=text, request=httpx.Request("GET", URL)
    )


@pytest.mark.asyncio
async def test_fetch_text_success() -> None:
    """HTTP 200 返回 body 文本"""
    with patch(
        "fetcher.fetcher.AsyncClient.get",
        return_value=_response(200, "hello"),
    ):
        fetcher = Fetcher(max_retries=0)
        result = await fetcher.fetch_text(URL)

    assert result == "hello"


@pytest.mark.asyncio
async def test_fetch_text_permanent_error_no_retry() -> None:
    """404（包未注册）属永久错误，立即返回 None 且不重试"""
    body = '{"code": 40400, "message": "包 \'xxx\' 未注册", "data": null}'
    get_mock = AsyncMock(return_value=_response(404, body))
    with patch("fetcher.fetcher.AsyncClient.get", get_mock):
        fetcher = Fetcher(max_retries=3, retry_wait=0)
        result = await fetcher.fetch_text(URL)

    assert result is None
    # 永久错误只请求一次
    assert get_mock.await_count == 1


@pytest.mark.asyncio
async def test_fetch_text_retryable_then_success() -> None:
    """503（数据未就绪）重试，后续 200 成功"""
    responses = [
        _response(503, '{"code": 50300, "message": "数据尚未就绪", "data": null}'),
        _response(200, "ok"),
    ]
    get_mock = AsyncMock(side_effect=responses)
    with patch("fetcher.fetcher.AsyncClient.get", get_mock):
        fetcher = Fetcher(max_retries=3, retry_wait=0)
        result = await fetcher.fetch_text(URL)

    assert result == "ok"
    assert get_mock.await_count == 2  # 首次失败 + 1 次重试


@pytest.mark.asyncio
async def test_fetch_text_retryable_exhausted() -> None:
    """502 持续失败，重试 max_retries 次后返回 None"""
    get_mock = AsyncMock(
        return_value=_response(
            502, '{"code": 50200, "message": "上游错误", "data": null}'
        )
    )
    with patch("fetcher.fetcher.AsyncClient.get", get_mock):
        fetcher = Fetcher(max_retries=2, retry_wait=0)
        result = await fetcher.fetch_text(URL)

    assert result is None
    # 首次 + 2 次重试 = 3 次
    assert get_mock.await_count == 3


@pytest.mark.asyncio
async def test_fetch_text_network_error_retried() -> None:
    """网络异常视为瞬时，重试后仍失败返回 None"""
    get_mock = AsyncMock(side_effect=httpx.ConnectError("boom"))
    with patch("fetcher.fetcher.AsyncClient.get", get_mock):
        fetcher = Fetcher(max_retries=1, retry_wait=0)
        result = await fetcher.fetch_text(URL)

    assert result is None
    assert get_mock.await_count == 2  # 首次 + 1 次重试


@pytest.mark.asyncio
async def test_fetch_text_no_retry_when_max_retries_zero() -> None:
    """max_retries=0 时网络异常只尝试一次"""
    get_mock = AsyncMock(side_effect=httpx.ConnectError("boom"))
    with patch("fetcher.fetcher.AsyncClient.get", get_mock):
        fetcher = Fetcher(max_retries=0)
        result = await fetcher.fetch_text(URL)

    assert result is None
    assert get_mock.await_count == 1


@pytest.mark.asyncio
async def test_extract_message_from_error_body() -> None:
    """错误 body 的 message 被提取（通过日志间接验证：永久错误路径不抛异常）"""
    body = '{"code": 42200, "message": "参数校验失败", "data": null}'
    get_mock = AsyncMock(return_value=_response(422, body))
    with patch("fetcher.fetcher.AsyncClient.get", get_mock):
        fetcher = Fetcher(max_retries=0)
        result = await fetcher.fetch_text(URL)

    assert result is None  # 422 永久错误


def test_fetcher_verify_ssl_default() -> None:
    """默认开启 SSL 证书校验（verify=True 传入 httpx 客户端）"""
    with patch("fetcher.fetcher.AsyncClient") as client_cls:
        Fetcher(max_retries=0)
    assert client_cls.call_args.kwargs["verify"] is True


def test_fetcher_verify_ssl_disabled() -> None:
    """verify_ssl=False 时禁用证书校验（verify=False 传入 httpx 客户端）"""
    with patch("fetcher.fetcher.AsyncClient") as client_cls:
        Fetcher(max_retries=0, verify_ssl=False)
    assert client_cls.call_args.kwargs["verify"] is False
