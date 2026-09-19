"""包配置同步：packages.toml 的声明式定义 → packages 表。

设计取舍：
- 每次启动都执行幂等 upsert（而非仅首次建库时），改配置重启即生效；
- ``enabled`` 不在 upsert 列内——它是运行期运维开关（改表 + reload），
  若随配置覆盖，临时禁用会在重启后静默失效，故仅对新增包生效；
- 配置中删除的包不自动删行（``ON DELETE CASCADE`` 会连带清掉版本/hash
  历史），保留并告警，删行须人工执行；
- 运行时校验（parser_type / archs / cron 语法）在此层做 fail-fast：
  config 层不依赖 constants/parsers（会循环导入），且 DB 行的宽容策略
  （registry_loader 逐行跳过）不适用于受信的配置文件来源。
"""

import json
import logging
from dataclasses import dataclass
from typing import Any

from apscheduler.triggers.cron import CronTrigger
from tortoise.transactions import in_transaction

from aur_metadata.config import PackageConfig
from aur_metadata.constants import ArchEnum
from aur_metadata.models import Package
from aur_metadata.parsers.registry import get_parser_types

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SyncReport:
    """一次同步的结果摘要（供 lifespan 记录与测试断言）"""

    created: list[str]
    updated: list[str]
    # DB 有而配置无的包：保留不动，仅告警
    orphans: list[str]


def _definition_fields(cfg: PackageConfig) -> dict[str, Any]:
    """PackageConfig → packages 表定义字段（不含 name / enabled / 时间戳）"""
    return {
        "parser_type": cfg.parser_type,
        "fetch_url": cfg.fetch_url,
        "archs": json.dumps(cfg.archs, separators=(",", ":")),
        "parser_config": (
            json.dumps(cfg.parser_config, separators=(",", ":"))
            if cfg.parser_config
            else None
        ),
        "schedule_type": cfg.schedule_type,
        "interval_seconds": cfg.interval_seconds,
        "cron_expr": cfg.cron_expr,
        "description": cfg.description,
    }


def _validate(packages: list[PackageConfig]) -> None:
    """对照运行时注册表校验配置，错误统一收集后抛 ``ValueError``"""
    known_parser_types: set[str] = set(get_parser_types())
    valid_archs: set[str] = {a.value for a in ArchEnum}
    errors: list[str] = []

    for cfg in packages:
        if cfg.parser_type not in known_parser_types:
            errors.append(
                f"包 {cfg.name}: 未注册的 parser_type {cfg.parser_type!r}"
                f"（可选：{sorted(known_parser_types)}）"
            )
        invalid_archs: list[str] = [a for a in cfg.archs if a not in valid_archs]
        if invalid_archs:
            errors.append(
                f"包 {cfg.name}: 非法 archs {invalid_archs}（可选：{sorted(valid_archs)}）"
            )
        if (cfg.interval_seconds is None) == (cfg.cron_expr is None):
            # 纵深防御：PackageConfig 可绕过 load_packages 直接构造，
            # 双空会触发 schema CHECK 的 IntegrityError，报错晦涩，这里提前拦截
            errors.append(
                f"包 {cfg.name}: interval_seconds 与 cron_expr 必须恰好一个非空"
            )
        if cfg.cron_expr is not None:
            try:
                CronTrigger.from_crontab(cfg.cron_expr)
            except ValueError:
                errors.append(f"包 {cfg.name}: 非法 cron 表达式 {cfg.cron_expr!r}")

    if errors:
        raise ValueError("包配置校验失败：\n- " + "\n- ".join(errors))


async def sync_packages_from_config(packages: list[PackageConfig]) -> SyncReport:
    """把包配置同步到 packages 表（按 name upsert 定义字段），返回摘要。

    整个 upsert 包在单事务内：任一行失败则整体回滚，不留半同步状态。
    定义字段无变化的行跳过写库——避免幂等重跑污染 ``updated_at`` 审计语义。
    """
    _validate(packages)

    created: list[str] = []
    updated: list[str] = []
    config_names: set[str] = set()

    async with in_transaction():
        for cfg in packages:
            config_names.add(cfg.name)
            fields: dict[str, Any] = _definition_fields(cfg)
            existing: Package | None = await Package.get_or_none(name=cfg.name)
            if existing is None:
                await Package.create(name=cfg.name, enabled=cfg.enabled, **fields)
                created.append(cfg.name)
                continue
            # enabled 保持 DB 现值，不随配置覆盖（见模块 docstring）
            changed: bool = False
            for key, value in fields.items():
                if getattr(existing, key) != value:
                    setattr(existing, key, value)
                    changed = True
            if changed:
                await existing.save()
                updated.append(cfg.name)

    db_names: set[str] = {row[0] for row in await Package.all().values_list("name")}
    orphans: list[str] = sorted(db_names - config_names)
    for name in orphans:
        logger.warning(
            "包 %s 存在于 packages 表但不在包配置中，已保留"
            "（定义不再随配置同步；确认不再需要请手动删行）",
            name,
        )

    logger.info(
        "包配置同步完成：新增 %d 个%s，更新 %d 个%s，未托管 %d 个%s",
        len(created),
        created,
        len(updated),
        updated,
        len(orphans),
        orphans,
    )
    return SyncReport(created=created, updated=updated, orphans=orphans)
