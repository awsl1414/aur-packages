"""app.services.registry_loader 集成测试（DB）。"""

from __future__ import annotations

from app.services.registry_loader import load_registry_from_db


async def test_loads_valid_packages(db, make_package) -> None:
    await make_package(name="qq", parser_type="qq")
    await make_package(name="wechat", parser_type="qq", archs='["x86_64"]')

    registry, pkgs = await load_registry_from_db()
    assert registry.get("qq") is not None
    assert registry.get("wechat") is not None
    assert {p.name for p in pkgs} == {"qq", "wechat"}


async def test_excludes_disabled(db, make_package) -> None:
    await make_package(name="qq", enabled=True)
    await make_package(name="old", enabled=False)

    _, pkgs = await load_registry_from_db()
    assert [p.name for p in pkgs] == ["qq"]


async def test_bad_parser_type_isolated(db, make_package, caplog) -> None:
    """未知 parser_type 的坏行被跳过，不阻塞其他包加载"""
    await make_package(name="good", parser_type="qq")
    await make_package(name="bad", parser_type="UNKNOWN_PARSER")

    with caplog.at_level("WARNING"):
        registry, pkgs = await load_registry_from_db()

    assert registry.get("good") is not None
    assert "bad" not in {p.name for p in pkgs}  # 坏行被排除
    assert {p.name for p in pkgs} == {"good"}
    assert any("bad" in r.getMessage() for r in caplog.records)


async def test_bad_archs_isolated(db, make_package) -> None:
    """非法 archs 值的坏行被跳过"""
    await make_package(name="good", parser_type="qq")
    await make_package(name="badarch", archs='["not-an-arch"]')

    registry, pkgs = await load_registry_from_db()
    assert registry.get("good") is not None
    assert "badarch" not in {p.name for p in pkgs}
    assert [p.name for p in pkgs] == ["good"]


async def test_all_bad_rows_returns_empty(db, make_package) -> None:
    """全部为坏行时不抛错，返回空集（单行错误不致全局失败）"""
    await make_package(name="bad1", parser_type="NOPE")
    await make_package(name="bad2", archs='["??"]')

    registry, pkgs = await load_registry_from_db()
    assert registry.list_all() == []
    assert pkgs == []
