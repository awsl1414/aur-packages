"""app.parsers.base 单元测试：_arch_value 与 _parse_json_dict 的缓存语义。"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

from app.constants import ArchEnum
from app.parsers import base as base_mod
from app.parsers.base import BaseParser


class _Concrete(BaseParser):
    """最小可实例化子类（实现抽象方法），用于测试基类行为"""

    def parse_version(self, response_data: str | Any) -> str | None:
        return None

    def parse_url(self, arch: ArchEnum | str, response_data: str | Any) -> str | None:
        return None


# ── _arch_value ──────────────────────────────────────────────────────────────


def test_arch_value_from_enum() -> None:
    assert BaseParser._arch_value(ArchEnum.X86_64) == "x86_64"


def test_arch_value_from_string() -> None:
    assert BaseParser._arch_value("aarch64") == "aarch64"


# ── _parse_json_dict 基本分支 ────────────────────────────────────────────────


def test_parse_json_dict_valid() -> None:
    assert _Concrete()._parse_json_dict('{"a": 1}') == {"a": 1}


def test_parse_json_dict_non_dict_json() -> None:
    """合法 JSON 但非对象（数组/数字）→ None"""
    assert _Concrete()._parse_json_dict("[1, 2, 3]") is None
    assert _Concrete()._parse_json_dict("42") is None


def test_parse_json_dict_invalid_json() -> None:
    assert _Concrete()._parse_json_dict("{not json") is None


# ── 缓存语义 ─────────────────────────────────────────────────────────────────


def test_cache_hits_same_response_object() -> None:
    """同一 response_data 对象多次调用只解析一次"""
    parser = _Concrete()
    resp = '{"a": 1}'
    with patch.object(base_mod.json, "loads", wraps=json.loads) as spy:
        assert parser._parse_json_dict(resp) == {"a": 1}
        assert parser._parse_json_dict(resp) == {"a": 1}
    assert spy.call_count == 1


def test_cache_invalidates_on_new_response() -> None:
    """新的 response_data 对象触发重新解析"""
    parser = _Concrete()
    with patch.object(base_mod.json, "loads", wraps=json.loads) as spy:
        parser._parse_json_dict('{"a": 1}')
        parser._parse_json_dict('{"b": 2}')
    assert spy.call_count == 2


def test_cache_bad_json_not_reparsed() -> None:
    """解析失败的响应对象也缓存（None），不重复尝试"""
    parser = _Concrete()
    bad = "{not json"
    with patch.object(base_mod.json, "loads", wraps=json.loads) as spy:
        assert parser._parse_json_dict(bad) is None
        assert parser._parse_json_dict(bad) is None
    assert spy.call_count == 1


def test_subclass_without_init_inherits_cache() -> None:
    """无自定义 __init__ 的子类继承缓存槽（QQParser/PyPIParser/ZenParser 即如此）"""
    parser = _Concrete()
    assert parser._cached_response is None
    parser._parse_json_dict('{"a": 1}')
    assert parser._cached_data == {"a": 1}
