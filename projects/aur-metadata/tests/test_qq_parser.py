"""aur_metadata.parsers.qq 单元测试（纯解析逻辑，不触网络）"""

from __future__ import annotations

import json
import logging
from typing import Any
from unittest.mock import patch

import pytest

from aur_metadata.constants import ArchEnum
from aur_metadata.parsers import qq as qq_mod
from aur_metadata.parsers.qq import QQParser
from tests.fakes import build_deb, make_app_config

_APP_CONFIG = make_app_config()
_PARSER = QQParser(_APP_CONFIG)


def _payload(**linux_overrides: Any) -> str:
    """构造 QQ pcConfig 响应，可覆盖 Linux 段字段"""
    linux: dict[str, Any] = {
        "version": "3.2.29",
        "x64DownloadUrl": {"deb": "https://x/QQ_3.2.29_260528_amd64_01.deb"},
        "armDownloadUrl": {"deb": "https://x/QQ_3.2.29_260528_arm64_01.deb"},
        "loongarchDownloadUrl": {
            "deb": "https://x/QQ_3.2.29_260528_loongarch64_01.deb"
        },
    }
    linux.update(linux_overrides)
    return json.dumps({"Linux": linux})


# ── version_from_package_head（统一 deb 机制）────────────────────────────────


def test_version_from_package_head_success() -> None:
    """deb control 段 Version 归一化：<upstream>_<revision>"""
    head = build_deb(version="3.2.29-260528")
    assert _PARSER.version_from_package_head(head) == "3.2.29_260528"


def test_version_from_package_head_bad_structure(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """头部非 deb 结构 → None 且走统一结构变更日志"""
    with caplog.at_level(logging.WARNING, logger="aur_metadata.parsers.qq"):
        assert _PARSER.version_from_package_head(b"garbage not a deb") is None
    assert "疑似上游结构变更" in caplog.text


# ── parse_url ────────────────────────────────────────────────────────────────


def test_parse_url_non_str_deb_value() -> None:
    """deb 值非字符串（如嵌套 dict）→ None（防垃圾 URL 流入签名/下载环节）"""
    payload = _payload(x64DownloadUrl={"deb": {"url": "https://x/QQ.deb"}})
    assert _PARSER.parse_url(ArchEnum.X86_64, payload) is None


def test_parse_url_each_arch(qq_response: str) -> None:
    url_x64 = _PARSER.parse_url(ArchEnum.X86_64, qq_response)
    url_arm = _PARSER.parse_url(ArchEnum.AARCH64, qq_response)
    url_loong = _PARSER.parse_url(ArchEnum.LOONG64, qq_response)
    assert url_x64 is not None and url_x64.endswith("_amd64_01.deb")
    assert url_arm is not None and url_arm.endswith("_arm64_01.deb")
    assert url_loong is not None and url_loong.endswith("_loongarch64_01.deb")


def test_parse_url_accepts_string_arch(qq_response: str) -> None:
    """arch 既可传 ArchEnum 也可传字符串值"""
    url = _PARSER.parse_url("aarch64", qq_response)
    assert url is not None and url.endswith("_arm64_01.deb")


def test_parse_url_unsupported_arch(qq_response: str) -> None:
    assert _PARSER.parse_url("mips64el", qq_response) is None


def test_parse_url_missing_arm_field() -> None:
    payload = _payload(armDownloadUrl=None)
    assert _PARSER.parse_url(ArchEnum.AARCH64, payload) is None


def test_parse_url_loongarch_as_plain_string() -> None:
    """loongarchDownloadUrl 既可能是 dict 也可能是裸字符串 URL"""
    payload = _payload(loongarchDownloadUrl="https://x/loong.deb")
    assert _PARSER.parse_url(ArchEnum.LOONG64, payload) == "https://x/loong.deb"


def test_parse_url_x64_as_plain_string() -> None:
    """裸字符串形态对各架构统一接受（对称化语义固化）"""
    payload = _payload(x64DownloadUrl="https://x/QQQ.deb")
    assert _PARSER.parse_url(ArchEnum.X86_64, payload) == "https://x/QQQ.deb"


# ── 跨方法缓存：多架构 parse_url 同一响应只解析一次 ─────────────────────────


def test_urls_share_single_parse(qq_response: str) -> None:
    """QQ 复用基类 _parse_json_dict 缓存，同一响应只 json 解析一次"""
    parser = QQParser(_APP_CONFIG)
    with patch.object(qq_mod.json, "loads", wraps=json.loads) as spy:
        parser.parse_url(ArchEnum.X86_64, qq_response)
        parser.parse_url(ArchEnum.AARCH64, qq_response)
    assert spy.call_count == 1
