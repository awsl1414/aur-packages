"""aur_metadata.parsers.deb 单元测试：DebParser 配置注入与 deb 头部版本提取。"""

from __future__ import annotations

import logging

import pytest

from aur_metadata.constants import ArchEnum
from aur_metadata.parsers.base import PackageFileVersionParser
from aur_metadata.parsers.deb import DebControlVersionMixin, DebParser
from aur_metadata.parsers.registry import get_parser
from tests.fakes import build_deb, make_app_config

_APP_CONFIG = make_app_config()

# ── 配置注入与架构别名 ────────────────────────────────────────────────────────


def test_urls_deb_arch_aliases_normalized() -> None:
    """deb 架构别名（amd64/arm64/loongarch64）归一化为 ArchEnum 值"""
    parser = DebParser(
        _APP_CONFIG,
        urls={
            "amd64": "https://x/app_amd64.deb",
            "arm64": "https://x/app_arm64.deb",
            "loongarch64": "https://x/app_loong.deb",
        }
    )
    assert parser.package_download_urls() == {
        ArchEnum.X86_64.value: "https://x/app_amd64.deb",
        ArchEnum.AARCH64.value: "https://x/app_arm64.deb",
        ArchEnum.LOONG64.value: "https://x/app_loong.deb",
    }


def test_urls_canonical_keys_passthrough() -> None:
    """直接使用 ArchEnum 值作键时不做改写"""
    parser = DebParser(_APP_CONFIG, urls={"x86_64": "https://x/app.deb"})
    assert parser.package_download_urls() == {"x86_64": "https://x/app.deb"}


def test_get_parser_deb_with_config() -> None:
    """parser_type=deb 经注册表构造，且具备安装包版本解析能力"""
    parser = get_parser("deb", {"urls": {"amd64": "https://x/a.deb"}}, app_config=_APP_CONFIG)
    assert isinstance(parser, DebParser)
    assert isinstance(parser, PackageFileVersionParser)
    assert isinstance(parser, DebControlVersionMixin)


def test_parse_version_always_none() -> None:
    """版本不来自文本响应（契约：服务层走 version_from_package_head）"""
    assert DebParser(_APP_CONFIG).parse_version("anything") is None


# ── parse_url（静态配置）─────────────────────────────────────────────────────


def test_parse_url_from_config() -> None:
    parser = DebParser(_APP_CONFIG, urls={"amd64": "https://x/app_amd64.deb"})
    assert parser.parse_url(ArchEnum.X86_64, "ignored") == "https://x/app_amd64.deb"
    assert parser.parse_url("x86_64", "ignored") == "https://x/app_amd64.deb"


def test_parse_url_unknown_arch_warns_and_none(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """未配置的架构属配置错误 → 普通告警 + None"""
    parser = DebParser(_APP_CONFIG, urls={"amd64": "https://x/app_amd64.deb"})
    with caplog.at_level(logging.WARNING, logger="aur_metadata.parsers.deb"):
        assert parser.parse_url(ArchEnum.AARCH64, "ignored") is None
    assert "aarch64" in caplog.text


# ── version_from_package_head ────────────────────────────────────────────────


def test_version_from_package_head_success() -> None:
    head = build_deb(version="3.14.0-7681")
    assert DebParser(_APP_CONFIG).version_from_package_head(head) == "3.14.0_7681"


def test_version_from_package_head_bad_structure(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """非 deb 结构 → None 且走统一结构变更日志"""
    parser = DebParser(_APP_CONFIG)
    with caplog.at_level(logging.WARNING, logger="aur_metadata.parsers.deb"):
        assert parser.version_from_package_head(b"garbage") is None
    assert "疑似上游结构变更" in caplog.text
