"""定时采集调度服务

基于 APScheduler 4：每包一个 schedule，按 ``packages`` 表的 schedule_type
（interval / cron）触发；采集与落库委托 PackageService.collect，本服务只负责
注册 schedule、执行采集回调。per-package 锁与节流均由 PackageService 持有。

scheduler 实例由 main.py 通过 ``async with AsyncScheduler()`` 管理生命周期。
"""

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler import AsyncScheduler, ConflictPolicy
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import SchedulerConfig
from app.models import Package
from app.schemas import PackageInfo
from app.services.package_service import PackageService
from app.services.registry_loader import load_registry_from_db

logger = logging.getLogger(__name__)


class ScheduleService:
    """定时采集调度服务"""

    def __init__(
        self,
        scheduler: AsyncScheduler,
        package_service: PackageService,
        scheduler_cfg: SchedulerConfig,
    ) -> None:
        self._scheduler = scheduler
        self._svc = package_service
        self._cfg = scheduler_cfg
        self._tz = ZoneInfo(scheduler_cfg.timezone)
        # schedule id → 配置签名：reload 时据此跳过未变更项，保留其计时避免重置
        self._schedule_signatures: dict[str, tuple[str, int | None, str | None]] = {}

    async def start(self, pkgs: list[Package]) -> None:
        """启动调度器并注册所有包的 schedule。

        ``pkgs`` 由 lifespan 从 ``load_registry_from_db`` 取得，避免重复查库。
        """
        for pkg in pkgs:
            await self._add_schedule(pkg, fire_now=self._cfg.run_on_startup)
        await self._scheduler.start_in_background()
        logger.info("定时采集调度器已启动，共 %d 个包", len(pkgs))

    async def _add_schedule(self, pkg: Package, fire_now: bool) -> None:
        """注册单个包的 schedule；id=``pkg-{id}``，conflict_policy=replace 便于 reload 更新。

        ``fire_now`` 控制 interval 模式首火：仅服务真正启动时按 run_on_startup 立即采集；
        reload 场景恒为 False（等下次自然触发），避免 reload 退化为全量立即采集。
        """
        await self._scheduler.add_schedule(
            self._collect,
            self._build_trigger(pkg, fire_now),
            id=f"pkg-{pkg.id}",
            kwargs={"package_id": pkg.id},
            max_jitter=self._cfg.jitter_seconds,
            misfire_grace_time=self._cfg.misfire_grace_seconds,
            conflict_policy=ConflictPolicy.replace,
        )
        self._schedule_signatures[f"pkg-{pkg.id}"] = self._schedule_signature(pkg)

    def _schedule_signature(self, pkg: Package) -> tuple[str, int | None, str | None]:
        """调度相关配置签名：变更才需重建 schedule"""
        return (pkg.schedule_type, pkg.interval_seconds, pkg.cron_expr)

    def _build_trigger(
        self, pkg: Package, fire_now: bool
    ) -> IntervalTrigger | CronTrigger:
        """按 schedule_type 构造触发器。

        cron：按表达式从下一个匹配时刻触发（天然不在启动即跑），用配置时区。
        interval：``fire_now=True`` 时启动即触发一次（仅服务启动且 run_on_startup 时）；
        否则把首次推迟一个间隔，避免 reload 或每次重启都把所有包采集一遍。
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
        if fire_now:
            return IntervalTrigger(seconds=pkg.interval_seconds)
        # 推迟首次触发到当前时刻 + 一个间隔
        start_time = datetime.now(self._tz) + timedelta(seconds=pkg.interval_seconds)
        return IntervalTrigger(seconds=pkg.interval_seconds, start_time=start_time)

    async def _collect(self, package_id: int) -> None:
        """定时回调：委托 PackageService 采集。全程兜底——单包失败不影响 scheduler"""
        try:
            pkg: Package = await Package.get(id=package_id)
        except Exception:
            logger.exception("package_id=%s 不存在，跳过采集", package_id)
            return

        try:
            await self._svc.collect(pkg.name)
        except Exception:
            # 域内失败（版本/hash）已由 svc 落库；此处仅兜底记录意外异常
            logger.exception("采集 %s 异常", pkg.name)

    async def collect_now(self, name: str) -> PackageInfo:
        """手动触发采集；异常上抛供路由层转 HTTP 错误。

        节流由 PackageService 判定（持 per-package 锁，消除 check-then-act），
        CollectThrottledError → 429，PackageNotFoundError → 404。
        """
        return await self._svc.collect_now(name)

    async def reload(self) -> list[str]:
        """重新从 DB 加载包配置并同步调度：重建 registry + schedule。

        覆盖 packages 表的新增、修改（fetch_url/archs/parser_type/schedule_*/enabled）
        与删除。返回当前 enabled 包名列表。

        - load_registry_from_db 已剔除坏行并只查一次库，此处复用其结果不再重复查询
        - 仅重建配置签名变更或新增的 schedule，未变更项保留计时，避免 reload 把
          interval next-fire 重置为 now+interval 而跳过即将到期的采集
        - reload 恒用 ``fire_now=False``，避免 reload 退化为全量立即采集
        - 清理已删除/停用包的运行时状态（svc 持有的锁与节流记录），防止内存只增不减
        """
        # 1. 重建内存 registry，复用 valid_pkgs 同步调度（不重复查库）
        new_registry, pkgs = await load_registry_from_db()
        self._svc.registry.replace_all(new_registry.list_all())

        # 2. 清理已删/停用包的运行时状态（锁 + 节流记录），reload 是天然清理时机
        enabled_names: set[str] = {p.name for p in pkgs}
        self._svc.prune_runtime(enabled_names)

        # 3. 同步 schedule：移除已停用/已删项，新增/更新变更项
        enabled_ids: set[int] = {p.id for p in pkgs}
        existing_ids: set[int] = {
            int(s.id.split("-", 1)[1])
            for s in await self._scheduler.get_schedules()
            if s.id.startswith("pkg-")
        }
        for pid in existing_ids - enabled_ids:
            await self._scheduler.remove_schedule(f"pkg-{pid}")
            self._schedule_signatures.pop(f"pkg-{pid}", None)
        for pkg in pkgs:
            sid: str = f"pkg-{pkg.id}"
            if self._schedule_signatures.get(sid) == self._schedule_signature(pkg):
                continue  # 调度配置未变更 → 保留现有计时
            await self._add_schedule(pkg, fire_now=False)

        logger.info("配置已重载，enabled=%d", len(pkgs))
        return [p.name for p in pkgs]

    async def stop(self) -> None:
        """停止调度器并等待彻底退出"""
        await self._scheduler.stop()
        await self._scheduler.wait_until_stopped()
        logger.info("定时采集调度器已停止")
