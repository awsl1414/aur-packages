from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from fetcher.fetcher import Fetcher

navicat_fech_url = "https://www.navicat.com.cn/products/navicat-premium-release-note#L"


@pytest.mark.asyncio
async def test_fetch_text_success():
    """正常返回文本"""
    mock_response = AsyncMock()
    mock_response.text = "hello"
    mock_response.raise_for_status = MagicMock(return_value=None)

    with patch("fetcher.fetcher.AsyncClient.get", return_value=mock_response):
        fetcher = Fetcher()
        result = await fetcher.fetch_text(navicat_fech_url)

    assert result == "hello"


@pytest.mark.asyncio
async def test_fetch_text_failure():
    """HTTP 错误时返回 None"""
    with patch(
        "fetcher.fetcher.AsyncClient.get",
        side_effect=httpx.HTTPStatusError(
            "boom",
            request=httpx.Request("GET", "http://invalid.url"),
            response=httpx.Response(500),
        ),
    ):
        fetcher = Fetcher()
        result = await fetcher.fetch_text("http://invalid.url")

    assert result is None
