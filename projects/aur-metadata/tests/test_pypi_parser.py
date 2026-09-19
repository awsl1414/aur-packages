"""aur_metadata.parsers.pypi 单元测试"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

from aur_metadata.constants import ArchEnum
from aur_metadata.parsers import base as base_mod
from aur_metadata.parsers.pypi import PyPIParser
from tests.fakes import make_app_config

_APP_CONFIG = make_app_config()
_PARSER = PyPIParser(_APP_CONFIG)


def _payload(**overrides: Any) -> str:
    """构造 PyPI JSON 响应，可覆盖 info / urls"""
    body: dict[str, Any] = {
        "info": {"version": "1.2.3"},
        "urls": [{"packagetype": "sdist", "url": "https://files/x-1.2.3.tar.gz"}],
    }
    body.update(overrides)
    return json.dumps(body)


# ── parse_version ────────────────────────────────────────────────────────────


def test_parse_version_success() -> None:
    assert _PARSER.parse_version(_payload()) == "1.2.3"


def test_parse_version_info_null() -> None:
    """info 键存在但值为 null（限流/错误载荷）→ None 且不抛 AttributeError"""
    assert _PARSER.parse_version(_payload(info=None)) is None


def test_parse_version_missing_info() -> None:
    assert _PARSER.parse_version(_payload(info={})) is None


def test_parse_version_missing_version_field() -> None:
    assert _PARSER.parse_version(_payload(info={"name": "x"})) is None


def test_parse_version_invalid_json() -> None:
    assert _PARSER.parse_version("{not json") is None


def test_parse_version_non_dict_json() -> None:
    assert _PARSER.parse_version("[]") is None


# ── parse_url ────────────────────────────────────────────────────────────────


def test_parse_url_returns_sdist() -> None:
    """sdist 与架构无关，任意 arch 返回同一 URL"""
    resp = _payload()
    assert _PARSER.parse_url("any", resp) == "https://files/x-1.2.3.tar.gz"
    assert _PARSER.parse_url(ArchEnum.X86_64, resp) == "https://files/x-1.2.3.tar.gz"


def test_parse_url_skips_non_sdist() -> None:
    """只取 packagetype=sdist，跳过 bdist"""
    resp = _payload(
        urls=[
            {"packagetype": "bdist_wheel", "url": "https://x.whl"},
            {"packagetype": "sdist", "url": "https://x.tar.gz"},
        ]
    )
    assert _PARSER.parse_url("any", resp) == "https://x.tar.gz"


def test_parse_url_no_sdist() -> None:
    resp = _payload(urls=[{"packagetype": "bdist_wheel", "url": "https://x.whl"}])
    assert _PARSER.parse_url("any", resp) is None


def test_parse_url_sdist_without_url_field() -> None:
    resp = _payload(urls=[{"packagetype": "sdist"}])
    assert _PARSER.parse_url("any", resp) is None


def test_parse_url_empty_urls() -> None:
    assert _PARSER.parse_url("any", _payload(urls=[])) is None


def test_parse_url_null_urls() -> None:
    """urls 键存在但值为 null → None 且不抛 TypeError"""
    assert _PARSER.parse_url("any", _payload(urls=None)) is None


def test_parse_url_invalid_json() -> None:
    assert _PARSER.parse_url("any", "{not json") is None


# ── 跨方法缓存：parse_version + parse_url 同一响应只解析一次 ─────────────────


def test_version_and_url_share_single_parse() -> None:
    parser = PyPIParser(_APP_CONFIG)
    resp = _payload()
    with patch.object(base_mod.json, "loads", wraps=json.loads) as spy:
        parser.parse_version(resp)
        parser.parse_url(ArchEnum.X86_64, resp)
        parser.parse_url("any", resp)
    assert spy.call_count == 1
