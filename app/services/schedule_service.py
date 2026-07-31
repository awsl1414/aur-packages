"""定时采集调度服务

基于 APScheduler 4：每包一个 schedule，按 ``packages`` 表的 schedule_type
（interval / cron）触发；采集复用 PackageService.get_info，结果落 versions/hashes。

scheduler 实例由 main.py 通过 ``async with AsyncScheduler()`` 管理生命周期，
本服务只负责注册 schedule、执行采集回调、落库。
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler import AsyncScheduler, ConflictPolicy
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import SchedulerConfig
from app.models import Package, PackageHash, PackageVersion
from app.schemas import PackageInfo
from app.services.package_service import (
    CollectThrottledError,
    PackageNotFoundError,
    PackageService,
)
from app.services.registry_loader import load_registry_from_db

logger = logging.getLogger(__name__)

_STATUS_SUCCESS = "success"
_STATUS_PARTIAL = "partial"
_STATUS_FAILED = "failed"


class ScheduleService:
    """定时采集调度服务"""

    def __init__(
        self,
        scheduler: AsyncScheduler,
        package_service: PackageService,
        name_to_id: dict[str, int],
        scheduler_cfg: SchedulerConfig,
    ) -> None:
        self._scheduler = scheduler
        self._svc = package_service
        self._name_to_id = name_to_id
        self._cfg = scheduler_cfg
        self._tz = ZoneInfo(scheduler_cfg.timezone)
        # a6 的 add_schedule 无 max_running_jobs，用 per-package 应用层锁保证同包不重入
        self._locks: dict[str, asyncio.Lock] = {}

    async def start(self) -> None:
        """启动调度器并注册所有 enabled 包的 schedule"""
        pkgs: list[Package] = await Package.filter(enabled=True)
        for pkg in pkgs:
            await self._add_schedule(pkg)
        await self._scheduler.start_in_background()
        logger.info("定时采集调度器已启动，共 %d 个包", len(pkgs))

    async def _add_schedule(self, pkg: Package) -> None:
        """注册单个包的 schedule；id=``pkg-{id}``，conflict_policy=replace 便于 reload"""
        await self._scheduler.add_schedule(
            self._collect,
            self._build_trigger(pkg),
            id=f"pkg-{pkg.id}",
            kwargs={"package_id": pkg.id},
            max_jitter=self._cfg.jitter_seconds,
            misfire_grace_time=self._cfg.misfire_grace_seconds,
            conflict_policy=ConflictPolicy.replace,
        )

    def _build_trigger(self, pkg: Package) -> IntervalTrigger | CronTrigger:
        """按 schedule_type 构造触发器。

        cron：按表达式从下一个匹配时刻触发（天然不在启动即跑），用配置时区。
        interval：run_on_startup=True 时启动即触发一次；False 时把首次推迟一个间隔，
        避免每次重启都把所有包采集一遍。
        """
        if pkg.schedule_type == "cron":
            # schema CHECK 保证 cron 模式下 cron_expr 非空
            if pkg.cron_expr is None:
                raise ValueError(f"包 {pkg.name} 配置为 cron 模式但缺少 cron_expr")
            return CronTrigger.from_crontab(pkg.cron_expr, timezone=self._tz)
        # schema CHECK 保证 interval 模式下 interval_seconds 非空
        if pkg.interval_seconds is None:
            raise ValueError(
                f"包 {pkg.name} 配置为 interval 模式但缺少 interval_seconds"
            )
        if self._cfg.run_on_startup:
            return IntervalTrigger(seconds=pkg.interval_seconds)
        # 推迟首次触发到当前时刻 + 一个间隔
        start_time = datetime.now(self._tz) + timedelta(seconds=pkg.interval_seconds)
        return IntervalTrigger(seconds=pkg.interval_seconds, start_time=start_time)

    async def _collect(self, package_id: int) -> None:
        """定时回调：采集并落库。全程兜底——单包失败不影响 scheduler 与其他包"""
        try:
            pkg: Package = await Package.get(id=package_id)
        except Exception:
            logger.exception("package_id=%s 不存在，跳过采集", package_id)
            return

        # 应用层锁：同包上次未完成时不重入（QQ 签名+下载较慢）
        async with self._locks.setdefault(pkg.name, asyncio.Lock()):
            try:
                info: PackageInfo = await self._svc.get_info(
                    pkg.name, hash_algorithm=pkg.hash_algorithm
                )
            except Exception as e:
                logger.exception("采集 %s 失败", pkg.name)
                await self._persist_failure(pkg, str(e))
                return

        await self._persist_success(pkg, info)

    async def collect_now(self, name: str) -> PackageInfo:
        """手动触发采集并落库；异常上抛供路由层转 HTTP 错误。

        节流内（距上次采集不足 min_collect_interval_seconds）抛 CollectThrottledError → 429。
        """
        pid: int | None = self._name_to_id.get(name)
        if pid is None:
            raise PackageNotFoundError(name)
        if self._svc.is_throttled(name):
            raise CollectThrottledError(name)
        pkg: Package = await Package.get(id=pid)
        info: PackageInfo = await self._svc.get_info(
            name, hash_algorithm=pkg.hash_algorithm
        )
        await self._persist_success(pkg, info)
        return info

    async def _persist_success(self, pkg: Package, info: PackageInfo) -> None:
        """按版本号与各架构 hash 命中情况判定 success/partial/failed 并落库"""
        hashes: dict[str, str | None] = info.hashes or {}
        expected_archs: set[str] = {a for a in json.loads(pkg.archs)}

        # 缺失的架构，或虽有记录但 hash 为 None 的架构
        bad: set[str] = expected_archs - set(hashes.keys())
        bad |= {a for a, v in hashes.items() if v is None}

        if not info.version:
            await self._persist_failure(pkg, "未解析到版本号")
            return
        if hashes and all(v is None for v in hashes.values()):
            await self._persist_failure(pkg, "全部架构 hash 计算失败")
            return
        status: str = _STATUS_PARTIAL if bad else _STATUS_SUCCESS

        version: PackageVersion = await PackageVersion.create(
            package=pkg, version=info.version, status=status, error=None
        )
        for arch_value, h in hashes.items():
            await PackageHash.create(
                version=version,
                arch=arch_value,
                algorithm=pkg.hash_algorithm,
                hash_value=h,
                url=info.urls.get(arch_value),
            )
        logger.info(
            "采集 %s 完成：version=%s status=%s", pkg.name, info.version, status
        )

    async def _persist_failure(self, pkg: Package, error: str) -> None:
        """记录失败快照便于审计"""
        await PackageVersion.create(
            package=pkg, version=None, status=_STATUS_FAILED, error=error
        )
        logger.warning("采集 %s 失败已记录：%s", pkg.name, error)

    async def reload(self) -> list[str]:
        """重新从 DB 加载包配置并同步调度：重建 registry + name_to_id + schedule。

        覆盖 packages 表的新增、修改（fetch_url/archs/parser_type/schedule_*/enabled）
        与删除。返回当前 enabled 包名列表。
        """
        # 1. 重建内存 registry：让 fetch_url/archs/parser 跟上 DB 最新值
        new_registry, name_to_id = await load_registry_from_db()
        self._svc.registry.replace_all(new_registry.list_all())
        self._name_to_id = name_to_id

        # 2. 同步 schedule：覆盖启用项，移除已停用/已删项
        enabled: list[Package] = await Package.filter(enabled=True)
        enabled_ids: set[str] = {f"pkg-{p.id}" for p in enabled}
        for pkg in enabled:
            await self._add_schedule(pkg)  # conflict_policy=replace 直接覆盖
        for sched in await self._scheduler.get_schedules():
            if sched.id.startswith("pkg-") and sched.id not in enabled_ids:
                await self._scheduler.remove_schedule(sched.id)

        logger.info("配置已重载，enabled=%d", len(enabled))
        return [p.name for p in enabled]

    async def stop(self) -> None:
        """停止调度器并等待彻底退出"""
        await self._scheduler.stop()
        await self._scheduler.wait_until_stopped()
        logger.info("定时采集调度器已停止")
