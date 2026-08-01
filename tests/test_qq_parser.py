"""app.parsers.qq 单元测试（纯解析逻辑，不触网络）"""

from __future__ import annotations

import json
from typing import Any

import pytest

from app.constants import ArchEnum
from app.parsers.qq import QQParser

_PARSER = QQParser()


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


# ── parse_version ────────────────────────────────────────────────────────────


def test_parse_version_success(qq_response: str) -> None:
    """合法响应返回 <api_version>_<build_number>"""
    assert _PARSER.parse_version(qq_response) == "3.2.29_260528"


@pytest.mark.parametrize(
    "bad",
    [
        None,
        123,
        b"bytes-not-str",
    ],
)
def test_parse_version_non_string_returns_none(bad: object) -> None:
    assert _PARSER.parse_version(bad) is None  # type: ignore[arg-type]


def test_parse_version_invalid_json() -> None:
    assert _PARSER.parse_version("{not json") is None


def test_parse_version_missing_linux_section() -> None:
    assert _PARSER.parse_version(json.dumps({"foo": {}})) is None


def test_parse_version_missing_version_field() -> None:
    assert _PARSER.parse_version(json.dumps({"Linux": {}})) is None


def test_parse_version_url_mismatch_returns_none() -> None:
    """API 版本与 deb URL 内版本不一致 → None（防 API/资源脱节）"""
    payload = _payload(
        version="9.9.9",  # 与 URL 中的 3.2.29 不一致
    )
    assert _PARSER.parse_version(payload) is None


def test_parse_version_url_without_amd64_pattern() -> None:
    """x64 deb URL 不含 _amd64 段 → 无法提取 build → None"""
    payload = _payload(
        x64DownloadUrl={"deb": "https://x/QQ_linux_x86_64.deb"},
    )
    assert _PARSER.parse_version(payload) is None


def test_parse_version_missing_x64_url() -> None:
    assert _PARSER.parse_version(_payload(x64DownloadUrl=None)) is None


# ── parse_url ────────────────────────────────────────────────────────────────


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


# ── _parse_response ──────────────────────────────────────────────────────────


def test_parse_response_non_dict_json() -> None:
    """合法 JSON 但非对象（如数组）→ None"""
    assert _PARSER._parse_response("[1, 2, 3]") is None


def test_parse_response_dict_passthrough() -> None:
    assert _PARSER._parse_response('{"a": 1}') == {"a": 1}
