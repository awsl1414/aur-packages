"""app.parsers.zen 单元测试"""

from __future__ import annotations

import json
from typing import Any

import pytest

from app.constants import ArchEnum
from app.parsers.zen import ZenParser

_PARSER = ZenParser()


def _payload(
    name: str = "Twilight build - 1.20t (2026-01-01)",
    assets: list[dict[str, Any]] | None = None,
) -> str:
    """构造 GitHub Releases JSON 响应"""
    return json.dumps(
        {
            "name": name,
            "assets": assets
            if assets is not None
            else [
                {
                    "name": "zen.linux-x86_64.tar.xz",
                    "browser_download_url": "https://z/x86.tar.xz",
                },
                {
                    "name": "zen.linux-aarch64.tar.xz",
                    "browser_download_url": "https://z/arm.tar.xz",
                },
            ],
        }
    )


# ── parse_version ────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "name,expected",
    [
        ("Twilight build - 1.20t (2026-01-01)", "1.20t"),
        ("Twilight build - 1.5a", "1.5a"),
        ("Twilight build - 2.0", "2.0"),
    ],
)
def test_parse_version_patterns(name: str, expected: str) -> None:
    assert _PARSER.parse_version(_payload(name=name)) == expected


@pytest.mark.parametrize("bad", [None, 123, b"x"])
def test_parse_version_non_string(bad: object) -> None:
    assert _PARSER.parse_version(bad) is None  # type: ignore[arg-type]


def test_parse_version_missing_name() -> None:
    assert _PARSER.parse_version(json.dumps({"assets": []})) is None


def test_parse_version_name_without_version_pattern() -> None:
    """release name 不含「数字.数字」片段 → None"""
    assert _PARSER.parse_version(_payload(name="just a build")) is None


def test_parse_version_invalid_json() -> None:
    assert _PARSER.parse_version("{not json") is None


# ── parse_url ────────────────────────────────────────────────────────────────


def test_parse_url_each_arch() -> None:
    resp = _payload()
    assert _PARSER.parse_url(ArchEnum.X86_64, resp) == "https://z/x86.tar.xz"
    assert _PARSER.parse_url(ArchEnum.AARCH64, resp) == "https://z/arm.tar.xz"


def test_parse_url_accepts_string_arch() -> None:
    assert _PARSER.parse_url("aarch64", _payload()) == "https://z/arm.tar.xz"


def test_parse_url_unsupported_arch() -> None:
    assert _PARSER.parse_url("mips64el", _payload()) is None


def test_parse_url_asset_without_download_url() -> None:
    """匹配到 asset 但无 browser_download_url → 继续找，最终 None"""
    resp = _payload(
        assets=[{"name": "zen.linux-x86_64.tar.xz"}]  # 缺 browser_download_url
    )
    assert _PARSER.parse_url(ArchEnum.X86_64, resp) is None


def test_parse_url_no_matching_asset() -> None:
    resp = _payload(
        assets=[{"name": "other.tar.xz", "browser_download_url": "https://z/o"}]
    )
    assert _PARSER.parse_url(ArchEnum.X86_64, resp) is None


def test_parse_url_empty_assets() -> None:
    assert _PARSER.parse_url(ArchEnum.X86_64, _payload(assets=[])) is None


def test_parse_url_non_string() -> None:
    assert _PARSER.parse_url(ArchEnum.X86_64, None) is None  # type: ignore[arg-type]
