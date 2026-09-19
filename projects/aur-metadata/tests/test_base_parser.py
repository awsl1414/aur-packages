"""aur_metadata.parsers.base 单元测试：_arch_value、_parse_json_dict 缓存与结构变更日志。"""

from __future__ import annotations

import json
import logging
from typing import Any
from unittest.mock import patch

import pytest

from aur_metadata.constants import ArchEnum
from aur_metadata.parsers import base as base_mod
from aur_metadata.parsers.base import _STRUCTURE_SNIPPET_MAX_LENGTH, BaseParser
from tests.fakes import make_app_config

_APP_CONFIG = make_app_config()


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
    assert _Concrete(_APP_CONFIG)._parse_json_dict('{"a": 1}') == {"a": 1}


def test_parse_json_dict_non_dict_json() -> None:
    """合法 JSON 但非对象（数组/数字）→ None"""
    assert _Concrete(_APP_CONFIG)._parse_json_dict("[1, 2, 3]") is None
    assert _Concrete(_APP_CONFIG)._parse_json_dict("42") is None


def test_parse_json_dict_invalid_json() -> None:
    assert _Concrete(_APP_CONFIG)._parse_json_dict("{not json") is None


# ── 缓存语义 ─────────────────────────────────────────────────────────────────


def test_cache_hits_same_response_object() -> None:
    """同一 response_data 对象多次调用只解析一次"""
    parser = _Concrete(_APP_CONFIG)
    resp = '{"a": 1}'
    with patch.object(base_mod.json, "loads", wraps=json.loads) as spy:
        assert parser._parse_json_dict(resp) == {"a": 1}
        assert parser._parse_json_dict(resp) == {"a": 1}
    assert spy.call_count == 1


def test_cache_invalidates_on_new_response() -> None:
    """新的 response_data 对象触发重新解析"""
    parser = _Concrete(_APP_CONFIG)
    with patch.object(base_mod.json, "loads", wraps=json.loads) as spy:
        parser._parse_json_dict('{"a": 1}')
        parser._parse_json_dict('{"b": 2}')
    assert spy.call_count == 2


def test_cache_bad_json_not_reparsed() -> None:
    """解析失败的响应对象也缓存（None），不重复尝试"""
    parser = _Concrete(_APP_CONFIG)
    bad = "{not json"
    with patch.object(base_mod.json, "loads", wraps=json.loads) as spy:
        assert parser._parse_json_dict(bad) is None
        assert parser._parse_json_dict(bad) is None
    assert spy.call_count == 1


def test_subclass_without_init_inherits_cache() -> None:
    """无自定义 __init__ 的子类继承缓存槽（QQParser/ZenParser 即如此）"""
    parser = _Concrete(_APP_CONFIG)
    assert parser._cached_response is None
    parser._parse_json_dict('{"a": 1}')
    assert parser._cached_data == {"a": 1}


# ── _log_structure_change 统一格式 ───────────────────────────────────────────


def test_log_structure_change_format(caplog: pytest.LogCaptureFixture) -> None:
    """统一格式：标记语 + 解析器名 + 详情 + 响应片段"""
    with caplog.at_level(logging.WARNING, logger="aur_metadata.parsers.base"):
        _Concrete(_APP_CONFIG)._log_structure_change("缺少 info.version 字段", '{"info": {}}')
    message: str = caplog.records[0].getMessage()
    assert "疑似上游结构变更" in message
    assert "_Concrete" in message
    assert "缺少 info.version 字段" in message
    assert '{"info": {}}' in message


def test_log_structure_change_snippet_truncated(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """超长响应片段截断，防止大响应刷屏"""
    with caplog.at_level(logging.WARNING, logger="aur_metadata.parsers.base"):
        _Concrete(_APP_CONFIG)._log_structure_change("d", "x" * 10_000)
    assert "x" * 10_000 not in caplog.records[0].getMessage()
    assert "x" * _STRUCTURE_SNIPPET_MAX_LENGTH in caplog.records[0].getMessage()


def test_log_structure_change_non_str_repr(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """非字符串 evidence 先 repr 再截断（None/bytes/子对象均可作证据）"""
    with caplog.at_level(logging.WARNING, logger="aur_metadata.parsers.base"):
        _Concrete(_APP_CONFIG)._log_structure_change("d", None)
    assert "None" in caplog.records[0].getMessage()


def test_invalid_json_logged_as_structure_change(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """JSON 解析失败（如 200 返回 HTML 错误页）走统一结构变更日志"""
    with caplog.at_level(logging.WARNING, logger="aur_metadata.parsers.base"):
        assert _Concrete(_APP_CONFIG)._parse_json_dict("<html>err</html>") is None
    assert "疑似上游结构变更" in caplog.text
