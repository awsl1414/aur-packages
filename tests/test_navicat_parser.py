"""app.parsers.navicat 单元测试"""

from __future__ import annotations

import pytest

from app.constants import ArchEnum
from app.parsers.navicat import NavicatParser

_URLS: dict[str, str] = {
    ArchEnum.X86_64.value: "https://download.navicat.com/navicat-premium-x86_64.AppImage",
    ArchEnum.AARCH64.value: "https://download.navicat.com/navicat-premium-aarch64.AppImage",
}


def _html(title: str = "Navicat Premium Lite (Linux) version 17.3.1") -> str:
    """构造 release-note HTML 片段"""
    return f"<html><body><h2>{title}</h2><p>released</p></body></html>"


# ── 构造 ─────────────────────────────────────────────────────────────────────


def test_default_urls_empty() -> None:
    assert NavicatParser()._urls == {}


def test_urls_injected() -> None:
    assert NavicatParser(urls=_URLS)._urls is _URLS


# ── parse_version（HTML 正则）────────────────────────────────────────────────


def test_parse_version_success() -> None:
    assert NavicatParser().parse_version(_html()) == "17.3.1"


@pytest.mark.parametrize("bad", [None, 123, b"x"])
def test_parse_version_non_string(bad: object) -> None:
    assert NavicatParser().parse_version(bad) is None  # type: ignore[arg-type]


def test_parse_version_case_insensitive() -> None:
    """正则 IGNORECASE：大小写不一也能匹配"""
    html = _html("NAVICAT PREMIUM (LINUX) VERSION 16.0.1")
    assert NavicatParser().parse_version(html) == "16.0.1"


def test_parse_version_skips_non_linux() -> None:
    """非 (Linux) 行（如 Windows）不匹配 → None"""
    html = _html("Navicat Premium (Windows) version 17.0.0")
    assert NavicatParser().parse_version(html) is None


def test_parse_version_no_version_number() -> None:
    """有 (Linux) 但无版本号 → None"""
    assert (
        NavicatParser().parse_version(_html("Navicat Premium (Linux) released")) is None
    )


def test_parse_version_html_without_match() -> None:
    assert NavicatParser().parse_version("<html>no version info here</html>") is None


# ── parse_url（配置注入，与响应无关）─────────────────────────────────────────


def test_parse_url_each_arch() -> None:
    parser = NavicatParser(urls=_URLS)
    # parse_url 不依赖 response_data（传占位即可）
    assert parser.parse_url(ArchEnum.X86_64, "ignored") == _URLS["x86_64"]
    assert parser.parse_url(ArchEnum.AARCH64, "ignored") == _URLS["aarch64"]


def test_parse_url_independent_of_response() -> None:
    """response_data 为 None 也能取到注入的 URL"""
    parser = NavicatParser(urls=_URLS)
    assert parser.parse_url(ArchEnum.X86_64, None) == _URLS["x86_64"]  # type: ignore[arg-type]


def test_parse_url_unsupported_arch() -> None:
    parser = NavicatParser(urls=_URLS)
    assert parser.parse_url("mips64el", "ignored") is None


def test_parse_url_empty_urls() -> None:
    assert NavicatParser().parse_url(ArchEnum.X86_64, "ignored") is None
