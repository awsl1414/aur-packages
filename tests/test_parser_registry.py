"""app.parsers.registry 单元测试"""

from __future__ import annotations

import pytest

from app.parsers.base import BaseParser
from app.parsers.qq import QQParser
from app.parsers.registry import _PARSER_REGISTRY, get_parser, register_parser


def test_get_parser_returns_new_instance() -> None:
    """已知 parser_type 返回新实例（parser 无状态，每次 new）"""
    p1 = get_parser("qq")
    p2 = get_parser("qq")
    assert isinstance(p1, QQParser)
    assert p1 is not p2


def test_get_parser_unknown_raises() -> None:
    with pytest.raises(ValueError):
        get_parser("not-a-real-parser")


def test_register_parser_adds_and_restores() -> None:
    """register_parser 注入新类型，测试后还原注册表避免污染其他用例"""

    class _Dummy(BaseParser):
        def parse_version(self, response_data: object) -> str | None:
            return None

        def parse_url(self, arch: object, response_data: object) -> str | None:
            return None

    assert "dummy" not in _PARSER_REGISTRY
    try:
        register_parser("dummy", _Dummy)
        assert isinstance(get_parser("dummy"), _Dummy)
    finally:
        _PARSER_REGISTRY.pop("dummy", None)
