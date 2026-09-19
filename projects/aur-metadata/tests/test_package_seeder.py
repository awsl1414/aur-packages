"""package_seeder 同步逻辑测试（upsert 幂等、enabled 归属、孤儿保留、fail-fast 校验）"""

from pathlib import Path
from typing import Any

import pytest
from tortoise import Tortoise, connections

from aur_metadata.config import PackageConfig, load_packages
from aur_metadata.db import _load_schema_sql, _split_sql
from aur_metadata.models import Package
from aur_metadata.services.package_seeder import sync_packages_from_config
from aur_metadata.services.registry_loader import load_registry_from_db
from tests.fakes import make_app_config

_APP_CONFIG = make_app_config()

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_PACKAGE_NAMES: set[str] = {
    "qq",
    "navicat",
    "bt-dualboot-ng",
    "trae",
    "trae-sg",
    "trae-us",
    "trae-cn",
    "zen-browser",
    "zcode",
}


def _cfg(name: str = "qq", **overrides: Any) -> PackageConfig:
    """构造一个合法 PackageConfig，测试按需覆盖字段"""
    defaults: dict[str, Any] = {
        "name": name,
        "parser_type": "qq",
        "fetch_url": "https://example.com/config.json",
        "archs": ["x86_64", "aarch64"],
        "parser_config": {},
        "enabled": True,
        "interval_seconds": 3600,
        "cron_expr": None,
        "description": None,
    }
    defaults.update(overrides)
    return PackageConfig(**defaults)


async def _get(name: str) -> Package:
    return await Package.get(name=name)


async def test_sync_creates_packages(db: None) -> None:
    report = await sync_packages_from_config(
        [_cfg("a"), _cfg("b", parser_config={"region": "sg"}, description="备注")]
    )

    assert report.created == ["a", "b"]
    pkg_a: Package = await _get("a")
    assert pkg_a.parser_type == "qq"
    assert pkg_a.fetch_url == "https://example.com/config.json"
    assert pkg_a.archs == '["x86_64","aarch64"]'
    assert pkg_a.parser_config is None  # 空 parser_config 落库为 NULL
    assert pkg_a.schedule_type == "interval"
    assert pkg_a.interval_seconds == 3600
    assert pkg_a.enabled is True

    pkg_b: Package = await _get("b")
    assert pkg_b.parser_config == '{"region":"sg"}'
    assert pkg_b.description == "备注"


async def test_sync_upsert_updates_definitions_keeps_enabled(
    db: None, make_package: Any
) -> None:
    """定义字段随配置更新；enabled 属运行期运维状态，不被配置覆盖"""
    await make_package(name="qq", fetch_url="https://old.example.com", enabled=False)
    report = await sync_packages_from_config(
        [_cfg("qq", fetch_url="https://new.example.com", interval_seconds=7200)]
    )

    assert report.updated == ["qq"]
    assert report.created == []
    pkg: Package = await _get("qq")
    assert pkg.fetch_url == "https://new.example.com"
    assert pkg.interval_seconds == 7200
    assert pkg.enabled is False


async def test_sync_idempotent(db: None) -> None:
    configs: list[PackageConfig] = [_cfg("a"), _cfg("b")]
    await sync_packages_from_config(configs)
    report = await sync_packages_from_config(configs)

    # 无变化的行跳过写库，不进 updated 列表（避免污染 updated_at 审计语义）
    assert report.created == []
    assert report.updated == []
    assert await Package.all().count() == 2


async def test_sync_cron_schedule(db: None) -> None:
    await sync_packages_from_config(
        [_cfg("c", interval_seconds=None, cron_expr="30 3 * * *")]
    )

    pkg: Package = await _get("c")
    assert pkg.schedule_type == "cron"
    assert pkg.cron_expr == "30 3 * * *"
    assert pkg.interval_seconds is None


async def test_sync_keeps_orphan_packages(db: None, make_package: Any) -> None:
    """配置中删掉的包保留在 DB（避免级联清掉采集历史），仅入摘要告警"""
    await make_package(name="legacy")

    report = await sync_packages_from_config([_cfg("a")])

    assert report.orphans == ["legacy"]
    assert await Package.filter(name="legacy").exists()
    assert await Package.filter(name="a").exists()


async def test_sync_readds_orphan_package(db: None, make_package: Any) -> None:
    """孤儿包重新加回配置 → 按 update 处理，enabled 沿用 DB 现值"""
    await make_package(name="legacy", enabled=False, fetch_url="https://old")

    report = await sync_packages_from_config([_cfg("legacy")])

    assert report.updated == ["legacy"]
    assert report.created == []
    assert report.orphans == []
    pkg: Package = await _get("legacy")
    assert pkg.fetch_url == "https://example.com/config.json"
    assert pkg.enabled is False


async def test_sync_disabled_new_package(db: None) -> None:
    await sync_packages_from_config([_cfg("a", enabled=False)])

    pkg: Package = await _get("a")
    assert pkg.enabled is False


async def test_sync_rejects_unknown_parser_type(db: None) -> None:
    with pytest.raises(ValueError, match="未注册的 parser_type"):
        await sync_packages_from_config([_cfg("a", parser_type="nope")])
    assert await Package.all().count() == 0


async def test_sync_rejects_invalid_arch(db: None) -> None:
    with pytest.raises(ValueError, match="非法 archs"):
        await sync_packages_from_config([_cfg("a", archs=["x86_64", "m1"])])


async def test_sync_rejects_invalid_cron(db: None) -> None:
    with pytest.raises(ValueError, match="非法 cron 表达式"):
        await sync_packages_from_config([_cfg("a", cron_expr="not a cron")])


async def test_sync_rejects_missing_schedule_fields(db: None) -> None:
    """绕过 load_packages 直接构造时，调度字段双空由 seeder 纵深拦截"""
    with pytest.raises(ValueError, match="恰好一个非空"):
        await sync_packages_from_config([_cfg("a", interval_seconds=None)])


async def test_sync_validates_before_writing(db: None) -> None:
    """校验先于写库整体执行：任一行非法则全量拒绝，不落任何一行"""
    with pytest.raises(ValueError):
        await sync_packages_from_config([_cfg("ok"), _cfg("bad", archs=["riscv"])])
    assert await Package.all().count() == 0


async def test_full_pipeline_with_real_schema_and_config(tmp_path: Path) -> None:
    """端到端：真实 schema.sql 建库 → 默认 packages.toml 同步 → 注册表加载。

    覆盖 STRICT 表 CHECK 约束对 upsert 数据的接受度，以及 seeder 与
    registry_loader 的字段序列化衔接（JSON 格式、parser_config 透传）。
    """
    await Tortoise.init(
        db_url=f"sqlite://{tmp_path / 'full.db'}",
        modules={"models": ["aur_metadata.models"]},
        _enable_global_fallback=True,
    )
    try:
        conn = connections.get("default")
        await conn.execute_query("PRAGMA foreign_keys = ON;")
        for stmt in _split_sql(_load_schema_sql()):
            await conn.execute_query(stmt)

        report = await sync_packages_from_config(
            load_packages(_PROJECT_ROOT / "configs" / "packages.toml")
        )
        assert set(report.created) == _DEFAULT_PACKAGE_NAMES
        assert report.updated == []
        assert report.orphans == []

        registry, pkgs = await load_registry_from_db(_APP_CONFIG)
        assert {e.name for e in registry.list_all()} == _DEFAULT_PACKAGE_NAMES
        assert {p.name for p in pkgs} == _DEFAULT_PACKAGE_NAMES
    finally:
        await Tortoise.close_connections()
