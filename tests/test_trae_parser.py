"""app.parsers.trae 单元测试"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import pytest

from app.constants import ArchEnum
from app.parsers import base as base_mod
from app.parsers.trae import TraeParser

# 构造含 cn/sg/va 三机房的 download[]（对齐上游真实结构）
_DOWNLOADS: list[dict[str, Any]] = [
    {
        "region": "cn",
        "x64.tar.gz": "https://cn/x64.tar.gz",
        "arm64.tar.gz": "https://cn/arm64.tar.gz",
    },
    {
        "region": "sg",
        "x64.tar.gz": "https://sg/x64.tar.gz",
        "arm64.tar.gz": "https://sg/arm64.tar.gz",
    },
    {
        "region": "va",
        "x64.tar.gz": "https://va/x64.tar.gz",
        "arm64.tar.gz": "https://va/arm64.tar.gz",
    },
]


def _payload(
    version: str = "2.1.0", downloads: list[dict[str, Any]] | None = None
) -> str:
    """构造 Trae manifest 响应（data.manifest.linux）"""
    return json.dumps(
        {
            "data": {
                "manifest": {
                    "linux": {
                        "version": version,
                        "download": downloads if downloads is not None else _DOWNLOADS,
                    }
                }
            }
        }
    )


# ── 构造与 region ────────────────────────────────────────────────────────────


def test_default_region_is_cn() -> None:
    assert TraeParser()._region == "cn"


# ── parse_version ────────────────────────────────────────────────────────────


def test_parse_version_success() -> None:
    assert TraeParser().parse_version(_payload("2.1.2")) == "2.1.2"


@pytest.mark.parametrize("bad", [None, 123, b"x"])
def test_parse_version_non_string(bad: object) -> None:
    assert TraeParser().parse_version(bad) is None  # type: ignore[arg-type]


def test_parse_version_missing_version() -> None:
    resp = json.dumps({"data": {"manifest": {"linux": {"download": _DOWNLOADS}}}})
    assert TraeParser().parse_version(resp) is None


def test_parse_version_missing_linux_section() -> None:
    assert TraeParser().parse_version(json.dumps({"data": {"manifest": {}}})) is None


def test_parse_version_invalid_json() -> None:
    assert TraeParser().parse_version("{not json") is None


# ── parse_url：region 选择 ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    "region,expected_host",
    [("cn", "cn"), ("sg", "sg"), ("va", "va")],
)
def test_parse_url_region_selection(region: str, expected_host: str) -> None:
    """不同 region 取对应机房 CDN 链接"""
    resp = _payload()
    url: str | None = TraeParser(region=region).parse_url(ArchEnum.X86_64, resp)
    assert url is not None and url.startswith(f"https://{expected_host}/")


def test_parse_url_each_arch() -> None:
    resp = _payload()
    parser = TraeParser(region="cn")
    assert parser.parse_url(ArchEnum.X86_64, resp) == "https://cn/x64.tar.gz"
    assert parser.parse_url(ArchEnum.AARCH64, resp) == "https://cn/arm64.tar.gz"


def test_parse_url_region_not_present() -> None:
    """download[] 中无该 region → None"""
    resp = _payload(downloads=[{"region": "cn", "x64.tar.gz": "https://cn/x64"}])
    assert TraeParser(region="va").parse_url(ArchEnum.X86_64, resp) is None


def test_parse_url_unsupported_arch() -> None:
    assert TraeParser().parse_url("mips64el", _payload()) is None


def test_parse_url_download_not_list() -> None:
    resp = json.dumps(
        {
            "data": {
                "manifest": {"linux": {"version": "1", "download": {"region": "cn"}}}
            }
        }
    )
    assert TraeParser().parse_url(ArchEnum.X86_64, resp) is None


def test_parse_url_non_string() -> None:
    assert TraeParser().parse_url(ArchEnum.X86_64, None) is None  # type: ignore[arg-type]


# ── 跨方法缓存：parse_version + 多架构 parse_url 同一响应只解析一次 ─────────


def test_version_and_urls_share_single_parse() -> None:
    parser = TraeParser(region="cn")
    resp = _payload()
    with patch.object(base_mod.json, "loads", wraps=json.loads) as spy:
        parser.parse_version(resp)
        parser.parse_url(ArchEnum.X86_64, resp)
        parser.parse_url(ArchEnum.AARCH64, resp)
    assert spy.call_count == 1
