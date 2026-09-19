"""aur_metadata.services.schedule_service 测试。

覆盖：trigger 构造、schedule 签名、collect_now 的节流/并发互斥/未找到、
_collect 落库与失败兜底、reload 的签名跳过与内存清理。

AsyncScheduler 用 FakeScheduler 桩替换（collect_now/reload 不依赖真实调度线程）。
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from aur_metadata.config import SchedulerConfig
from aur_metadata.constants import ArchEnum
from aur_metadata.models import PackageVersion
from aur_metadata.services.package_service import (
    CollectThrottledError,
    PackageNotFoundError,
    PackageService,
)
from aur_metadata.services.schedule_service import ScheduleService
from tests.fakes import FakeFetcher, make_app_config, make_qq_registry

_PKG_ID = 1


# ── 辅助构造 ─────────────────────────────────────────────────────────────────


def _cfg() -> SchedulerConfig:
    return SchedulerConfig(
        enabled=True,
        timezone="Asia/Shanghai",
        jitter_seconds=0,
        misfire_grace_seconds=300,
        min_collect_interval_seconds=300,
        run_on_startup=False,
    )


class FakeScheduler:
    """记录调度的桩，模拟 AsyncScheduler 的子集接口。"""

    def __init__(self, existing_ids: list[str] | None = None) -> None:
        self.added: list[str] = []
        self.removed: list[str] = []
        self.schedules: list[SimpleNamespace] = [
            SimpleNamespace(id=i) for i in (existing_ids or [])
        ]

    async def add_schedule(
        self, func: Any, trigger: Any, *, id: str, kwargs: Any = None, **_: Any
    ) -> None:
        self.added.append(id)

    async def get_schedules(self) -> list[SimpleNamespace]:
        return list(self.schedules)

    async def remove_schedule(self, schedule_id: str) -> None:
        self.removed.append(schedule_id)
        self.schedules = [s for s in self.schedules if s.id != schedule_id]

    async def start_in_background(self) -> None: ...

    async def stop(self) -> None: ...

    async def wait_until_stopped(self) -> None: ...


def _svc(fetcher: FakeFetcher | None = None) -> PackageService:
    """单包 'qq'（x86_64）的 PackageService；fetcher 可注入（并发测试用）。"""
    f = fetcher or FakeFetcher(text="cfg", hashes={"x86_64": "h1"})
    return PackageService(f.as_fetcher(), make_qq_registry([ArchEnum.X86_64]), 300)


def _build_service(svc: PackageService, scheduler: FakeScheduler) -> ScheduleService:
    # FakeScheduler 与 AsyncScheduler 同构（鸭子类型），用 type: ignore 绕过 ty 静态检查
    return ScheduleService(scheduler, svc, _cfg(), make_app_config())  # type: ignore


def _pkg(**kw: Any) -> Any:
    """仅含调度相关字段的轻量 Package 替身（SimpleNamespace）"""
    defaults: dict[str, Any] = {
        "id": _PKG_ID,
        "name": "qq",
        "schedule_type": "interval",
        "interval_seconds": 3600,
        "cron_expr": None,
    }
    defaults.update(kw)
    return SimpleNamespace(**defaults)


# ── _build_trigger ───────────────────────────────────────────────────────────


def test_build_trigger_interval_fire_now() -> None:
    service = _build_service(_svc(), FakeScheduler())
    assert isinstance(service._build_trigger(_pkg(), fire_now=True), IntervalTrigger)


def test_build_trigger_interval_deferred_has_future_start() -> None:
    """fire_now=False 时首次推迟一个间隔，避免 reload/重启立即全量采集"""
    service = _build_service(_svc(), FakeScheduler())
    before = datetime.now(ZoneInfo("Asia/Shanghai"))
    trig = service._build_trigger(_pkg(interval_seconds=100), fire_now=False)
    assert isinstance(trig, IntervalTrigger)
    assert trig.start_time > before  # 推迟到未来


def test_build_trigger_cron() -> None:
    service = _build_service(_svc(), FakeScheduler())
    trig = service._build_trigger(
        _pkg(schedule_type="cron", interval_seconds=None, cron_expr="30 3 * * *"),
        fire_now=False,
    )
    assert isinstance(trig, CronTrigger)


def test_build_trigger_cron_missing_expr_raises() -> None:
    service = _build_service(_svc(), FakeScheduler())
    with pytest.raises(ValueError):
        service._build_trigger(
            _pkg(schedule_type="cron", interval_seconds=None, cron_expr=None),
            fire_now=False,
        )


def test_build_trigger_interval_missing_seconds_raises() -> None:
    service = _build_service(_svc(), FakeScheduler())
    with pytest.raises(ValueError):
        service._build_trigger(
            _pkg(schedule_type="interval", interval_seconds=None), fire_now=False
        )


def test_schedule_signature_tracks_config() -> None:
    service = _build_service(_svc(), FakeScheduler())
    assert service._schedule_signature(_pkg()) == ("interval", 3600, None)
    assert service._schedule_signature(
        _pkg(schedule_type="cron", interval_seconds=None, cron_expr="* * * * *")
    ) == ("cron", None, "* * * * *")


# ── collect_now ──────────────────────────────────────────────────────────────


async def test_collect_now_unknown_package() -> None:
    """name 不在 registry → PackageNotFoundError，无需 DB"""
    service = _build_service(_svc(), FakeScheduler())
    with pytest.raises(PackageNotFoundError):
        await service.collect_now("ghost")


async def test_collect_now_throttled() -> None:
    """节流窗口内 → CollectThrottledError，在 Package.get 前抛出，无需 DB"""
    svc = _svc()
    svc._last_collected["qq"] = datetime.now(UTC)
    service = _build_service(svc, FakeScheduler())
    with pytest.raises(CollectThrottledError):
        await service.collect_now("qq")


async def test_collect_now_success_persists(db, make_package) -> None:
    pkg = await make_package()
    service = _build_service(_svc(), FakeScheduler())
    info = await service.collect_now("qq")
    assert info.version == "1.0.0"
    v = await PackageVersion.get(package=pkg)
    assert v.status == "success"


async def test_collect_now_concurrent_second_is_throttled(db, make_package) -> None:
    """并发两次手动刷新：第一次持锁慢采集，第二次等锁后命中节流 → 429。

    用 FakeFetcher.entered 事件确定性等待第一次真正进入 fetch_text（已过锁与节流
    检查），再发起第二次——替代基于 sleep 的时序假设，避免 CI 高负载下 flaky。
    """
    await make_package()
    entered = asyncio.Event()
    fetcher = FakeFetcher(
        text="cfg", hashes={"x86_64": "h1"}, delay=0.2, entered=entered
    )
    service = _build_service(_svc(fetcher), FakeScheduler())

    first = asyncio.create_task(service.collect_now("qq"))
    await entered.wait()  # 第一次已持锁并在 fetch 中
    with pytest.raises(CollectThrottledError):
        await service.collect_now("qq")
    await first
    assert fetcher.text_calls == 1  # 第二次未真正回源


# ── _collect ─────────────────────────────────────────────────────────────────


async def test_collect_missing_package_logged(db) -> None:
    """不存在的 package_id：Package.get 抛错被捕获、只记日志、不影响调度器"""
    service = _build_service(_svc(), FakeScheduler())
    await service._collect(999999)  # 不应抛


async def test_collect_failure_records_failed(db, make_package) -> None:
    """版本抓取失败 → svc 落 failed 审计行，_collect 不逃逸到调度器"""
    pkg = await make_package()
    svc = _svc(FakeFetcher(text=None))  # 版本源失败
    service = _build_service(svc, FakeScheduler())
    await service._collect(pkg.id)  # 不抛
    v = await PackageVersion.get(package=pkg)
    assert v.status == "failed" and v.version is None and v.error


# ── reload ───────────────────────────────────────────────────────────────────


async def test_reload_skips_unchanged_schedules(db, make_package) -> None:
    """调度配置未变更的包不重建 schedule（保留计时），仅变更项才 add_schedule"""
    await make_package(name="qq", interval_seconds=3600)
    sched = FakeScheduler(existing_ids=["pkg-1"])  # qq.id==1 已存在
    service = _build_service(_svc(), sched)
    service._schedule_signatures["pkg-1"] = ("interval", 3600, None)  # 与 DB 一致

    names = await service.reload()
    assert names == ["qq"]
    assert sched.added == [] and sched.removed == []


async def test_reload_rebuilds_changed_schedule(db, make_package) -> None:
    """interval 变更 → 签名不同 → 重建 schedule"""
    await make_package(name="qq", interval_seconds=1800)
    sched = FakeScheduler(existing_ids=["pkg-1"])
    service = _build_service(_svc(), sched)
    service._schedule_signatures["pkg-1"] = ("interval", 3600, None)  # 旧值

    await service.reload()
    assert sched.added == ["pkg-1"]


async def test_reload_removes_disabled_and_cleans_memory(db, make_package) -> None:
    """已停用包：移除 schedule，并清理 svc 持有的 _locks / _last_collected"""
    await make_package(name="qq", enabled=False)
    sched = FakeScheduler(existing_ids=["pkg-1"])
    svc = _svc()
    service = _build_service(svc, sched)
    svc._locks["qq"] = asyncio.Lock()
    svc._last_collected["qq"] = datetime.now(UTC)

    await service.reload()
    assert sched.removed == ["pkg-1"]
    assert "qq" not in svc._locks
    assert "qq" not in svc._last_collected
