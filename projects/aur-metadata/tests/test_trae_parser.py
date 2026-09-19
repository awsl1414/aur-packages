"""app.parsers.trae 单元测试"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import pytest

from app.constants import ArchEnum
from app.parsers import base as base_mod
from app.parsers.trae import TraeParser

# 上游当前结构：manifest.linux 无 version 字段，版本号内嵌于链接路径
_VERSION = "2.3.77497"


def _entry(region: str, host: str) -> dict[str, Any]:
    """构造单个 region 的 download 项（对齐上游真实结构）"""
    base = f"https://{host}/obj/pkg/app/releases/stable/{_VERSION}/linux"
    return {
        "region": region,
        "x64.tar.gz": f"{base}/TraeCode_CN-linux-x64.tar.gz",
        "arm64.tar.gz": f"{base}/TraeCode_CN-linux-arm64.tar.gz",
    }


# 构造含 cn/sg/va 三机房的 download[]（对齐上游真实结构）
_DOWNLOADS: list[dict[str, Any]] = [
    _entry("cn", "cn-cdn"),
    _entry("sg", "sg-cdn"),
    _entry("va", "va-cdn"),
]


def _payload(downloads: list[dict[str, Any]] | None = None) -> str:
    """构造 Trae manifest 响应（data.manifest.linux，无独立 version 字段）"""
    linux: dict[str, Any] = {
        "download": downloads if downloads is not None else _DOWNLOADS
    }
    return json.dumps({"data": {"manifest": {"linux": linux}}})


# ── 构造与 region ────────────────────────────────────────────────────────────


def test_default_region_is_cn() -> None:
    assert TraeParser()._region == "cn"


# ── parse_version ────────────────────────────────────────────────────────────


def test_parse_version_from_url() -> None:
    """从 download 链接路径提取版本号（上游无独立 version 字段）"""
    assert TraeParser().parse_version(_payload()) == _VERSION


@pytest.mark.parametrize(
    "x64_url,arm64_url,expected",
    [
        # 各架构版本一致 → 提取成功
        (
            "https://cn/releases/stable/2.3.77497/x64.tar.gz",
            "https://cn/releases/stable/2.3.77497/arm64.tar.gz",
            "2.3.77497",
        ),
        # x64/arm64 版本分叉（上游部分发布）→ 拒绝返回
        (
            "https://cn/releases/stable/2.3.77497/x64.tar.gz",
            "https://cn/releases/stable/2.3.77496/arm64.tar.gz",
            None,
        ),
    ],
)
def test_parse_version_cross_arch_consistency(
    x64_url: str, arm64_url: str, expected: str | None
) -> None:
    """各架构链接版本不一致时拒绝返回，防 hash 挂错版本号"""
    entry: dict[str, Any] = {
        "region": "cn",
        "x64.tar.gz": x64_url,
        "arm64.tar.gz": arm64_url,
    }
    resp = json.dumps({"data": {"manifest": {"linux": {"download": [entry]}}}})
    assert TraeParser().parse_version(resp) == expected


def test_parse_version_ignores_non_arch_fields() -> None:
    """版本只从架构链接 key 提取；其他字符串字段含版本段不干扰"""
    entry: dict[str, Any] = {
        "region": "cn",
        "notes": "升级到 /releases/stable/9.9.9/ 说明",
        "x64.tar.gz": f"https://cn/releases/stable/{_VERSION}/x64.tar.gz",
        "arm64.tar.gz": f"https://cn/releases/stable/{_VERSION}/arm64.tar.gz",
    }
    resp = json.dumps({"data": {"manifest": {"linux": {"download": [entry]}}}})
    assert TraeParser().parse_version(resp) == _VERSION


def test_parse_version_version_last_segment() -> None:
    """版本段为路径最后一段（无尾斜杠）同样可提取"""
    entry: dict[str, Any] = {
        "region": "cn",
        "x64.tar.gz": f"https://cn/releases/stable/{_VERSION}",
        "arm64.tar.gz": f"https://cn/releases/stable/{_VERSION}/arm64.tar.gz",
    }
    resp = json.dumps({"data": {"manifest": {"linux": {"download": [entry]}}}})
    assert TraeParser().parse_version(resp) == _VERSION


def test_parse_version_no_version_segment_in_urls() -> None:
    """无 version 字段且链接不含版本段 → None"""
    resp = json.dumps(
        {
            "data": {
                "manifest": {
                    "linux": {
                        "download": [
                            {"region": "cn", "x64.tar.gz": "https://cn/x64.tar.gz"}
                        ]
                    }
                }
            }
        }
    )
    assert TraeParser().parse_version(resp) is None


def test_parse_version_missing_download() -> None:
    resp = json.dumps({"data": {"manifest": {"linux": {}}}})
    assert TraeParser().parse_version(resp) is None


def test_parse_version_missing_linux_section() -> None:
    assert TraeParser().parse_version(json.dumps({"data": {"manifest": {}}})) is None


def test_parse_version_invalid_json() -> None:
    assert TraeParser().parse_version("{not json") is None


# ── parse_url：region 选择 ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    "region,expected_host",
    [("cn", "cn-cdn"), ("sg", "sg-cdn"), ("va", "va-cdn")],
)
def test_parse_url_region_selection(region: str, expected_host: str) -> None:
    """不同 region 取对应机房 CDN 链接"""
    resp = _payload()
    url: str | None = TraeParser(region=region).parse_url(ArchEnum.X86_64, resp)
    assert url is not None and url.startswith(f"https://{expected_host}/")


def test_parse_url_each_arch() -> None:
    resp = _payload()
    parser = TraeParser(region="cn")
    assert (
        parser.parse_url(ArchEnum.X86_64, resp)
        == f"https://cn-cdn/obj/pkg/app/releases/stable/{_VERSION}/linux/TraeCode_CN-linux-x64.tar.gz"
    )
    assert (
        parser.parse_url(ArchEnum.AARCH64, resp)
        == f"https://cn-cdn/obj/pkg/app/releases/stable/{_VERSION}/linux/TraeCode_CN-linux-arm64.tar.gz"
    )


def test_parse_url_region_not_present() -> None:
    """download[] 中无该 region → None"""
    resp = _payload(downloads=[_entry("cn", "cn-cdn")])
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


# ── 跨方法缓存：parse_version + 多架构 parse_url 同一响应只解析一次 ─────────


def test_version_and_urls_share_single_parse() -> None:
    parser = TraeParser(region="cn")
    resp = _payload()
    with patch.object(base_mod.json, "loads", wraps=json.loads) as spy:
        parser.parse_version(resp)
        parser.parse_url(ArchEnum.X86_64, resp)
        parser.parse_url(ArchEnum.AARCH64, resp)
    assert spy.call_count == 1
