"""aur_metadata.parsers.zen 单元测试"""

from __future__ import annotations

import json
from typing import Any

import pytest

from aur_metadata.constants import ArchEnum
from aur_metadata.parsers.zen import ZenParser
from tests.fakes import make_app_config

_APP_CONFIG = make_app_config()
_PARSER = ZenParser(_APP_CONFIG)


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
        ("Twilight build - 1.22t (2026-08-01 at 23:18:32)", "1.22t.20260801"),
        ("Twilight build - 1.20t (2026-01-01)", "1.20t.20260101"),
        ("Twilight build - 1.5a", "1.5a"),  # 无日期 → 仅版本号
        ("Twilight build - 2.0", "2.0"),  # 无日期 → 仅版本号
    ],
)
def test_parse_version_patterns(name: str, expected: str) -> None:
    assert _PARSER.parse_version(_payload(name=name)) == expected


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


def test_parse_url_null_assets() -> None:
    """assets 键存在但值为 null → None 且不抛 TypeError（helper 的 None 表默认，故直构）"""
    resp = json.dumps({"name": "Twilight build", "assets": None})
    assert _PARSER.parse_url(ArchEnum.X86_64, resp) is None
