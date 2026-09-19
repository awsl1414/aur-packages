"""aur_metadata.parsers.registry 单元测试"""

from __future__ import annotations

import pytest

from aur_metadata.parsers.base import BaseParser
from aur_metadata.parsers.deb import DebParser
from aur_metadata.parsers.navicat import NavicatParser
from aur_metadata.parsers.qq import QQParser
from aur_metadata.parsers.registry import _PARSER_REGISTRY, get_parser, register_parser
from tests.fakes import make_app_config
from aur_metadata.parsers.trae import TraeParser


_APP_CONFIG = make_app_config()


def test_get_parser_returns_new_instance() -> None:
    """已知 parser_type 返回新实例（parser 无状态，每次 new）"""
    p1 = get_parser("qq", app_config=_APP_CONFIG)
    p2 = get_parser("qq", app_config=_APP_CONFIG)
    assert isinstance(p1, QQParser)
    assert p1 is not p2


def test_get_parser_unknown_raises() -> None:
    with pytest.raises(ValueError):
        get_parser("not-a-real-parser", app_config=_APP_CONFIG)


# ── parser_config 注入：get_parser(parser_type, config) 透传 cls(**config) ──


def test_get_parser_trae_default_region() -> None:
    """无 config 时 TraeParser 默认 region=cn"""
    parser = get_parser("trae", app_config=_APP_CONFIG)
    assert isinstance(parser, TraeParser)
    assert parser._region == "cn"


def test_get_parser_trae_with_region_config() -> None:
    parser = get_parser("trae", {"region": "sg"}, app_config=_APP_CONFIG)
    assert isinstance(parser, TraeParser)
    assert parser._region == "sg"


def test_get_parser_navicat_with_urls_config() -> None:
    urls = {"x86_64": "https://x/n.AppImage"}
    parser = get_parser("navicat", {"urls": urls}, app_config=_APP_CONFIG)
    assert isinstance(parser, NavicatParser)
    assert parser._urls == urls


def test_get_parser_deb_with_urls_config() -> None:
    parser = get_parser("deb", {"urls": {"amd64": "https://x/a.deb"}}, app_config=_APP_CONFIG)
    assert isinstance(parser, DebParser)
    assert parser._urls == {"x86_64": "https://x/a.deb"}


def test_get_parser_empty_config_is_no_arg() -> None:
    """空 dict 等价无参构造（与 config=None 行为一致）"""
    assert isinstance(get_parser("qq", {}, app_config=_APP_CONFIG), QQParser)


def test_get_parser_unknown_config_key_raises() -> None:
    """config 含未知构造参数 → TypeError（cls(**config) 透传）"""
    with pytest.raises(TypeError):
        get_parser("qq", {"bogus": 1}, app_config=_APP_CONFIG)  # type: ignore[arg-type]


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
        assert isinstance(get_parser("dummy", app_config=_APP_CONFIG), _Dummy)
    finally:
        _PARSER_REGISTRY.pop("dummy", None)
