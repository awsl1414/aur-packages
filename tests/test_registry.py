"""app.registry 单元测试"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.constants import ArchEnum
from app.parsers.base import BaseParser
from app.parsers.qq import QQParser
from app.registry import PackageEntry, PackageRegistry


def _entry(name: str) -> PackageEntry:
    return PackageEntry(
        name=name,
        parser=QQParser(),
        fetch_url="https://example.com",
        archs=[ArchEnum.X86_64],
    )


def test_replace_all_rebuilds_from_scratch() -> None:
    """replace_all 整体替换，旧条目被清空"""
    reg = PackageRegistry()
    reg.replace_all([_entry("a"), _entry("b")])
    assert {e.name for e in reg.list_all()} == {"a", "b"}

    reg.replace_all([_entry("c")])
    assert {e.name for e in reg.list_all()} == {"c"}


def test_get_hit_and_miss() -> None:
    reg = PackageRegistry()
    reg.replace_all([_entry("qq")])
    hit = reg.get("qq")
    assert hit is not None
    assert hit.name == "qq"
    assert reg.get("nope") is None


def test_list_all_returns_copy() -> None:
    """list_all 返回列表副本，外部修改不影响内部存储"""
    reg = PackageRegistry()
    reg.replace_all([_entry("qq")])
    items = reg.list_all()
    items.clear()
    assert reg.get("qq") is not None


def test_entry_is_frozen() -> None:
    """PackageEntry 为不可变 dataclass，赋值应抛 FrozenInstanceError"""
    e = _entry("qq")
    with pytest.raises(FrozenInstanceError):
        e.name = "hack"  # type: ignore  # 故意违反 frozen


def test_entry_holds_parser_instance() -> None:
    """entry.parser 是 BaseParser 子类实例"""
    e = _entry("qq")
    assert isinstance(e.parser, BaseParser)
