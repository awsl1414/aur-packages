"""aur_metadata.services.package_service 集成测试（DB + Fake 桩）。

覆盖解耦后的新契约：
- 节流 / 运行时清理（纯逻辑）
- get_info 纯 DB 读、不触网；无快照 → DataNotReadyError
- collect：version 与 hash 独立落库；version 成功 + hash 全失败时 version 仍可读（核心回归）
- 每次 collect 都重新下载算 hash（无短路）
- 版本抓取失败 → 落 failed 行并抛 RuntimeError
- collect_now 节流 → CollectThrottledError
- get_info stale → fire-and-forget 后台刷新
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import cast

import pytest

from aur_metadata.constants import ArchEnum
from aur_metadata.models import PackageHash, PackageVersion
from aur_metadata.services.package_service import (
    CollectThrottledError,
    DataNotReadyError,
    PackageNotFoundError,
    PackageService,
)
from tests.fakes import FakeFetcher, make_qq_registry


def _service(
    text: str | None = "",
    hashes: dict[str, str | None] | None = None,
    interval: int = 0,
    stale_seconds: int = 0,
) -> PackageService:
    """构造一个指向单包 'qq'（双架构）registry 的 PackageService。"""
    return PackageService(
        FakeFetcher(text=text, hashes=hashes).as_fetcher(),
        make_qq_registry([ArchEnum.X86_64, ArchEnum.AARCH64], version="1.2.3"),
        min_collect_interval_seconds=interval,
        version_stale_seconds=stale_seconds,
    )


# ── 纯逻辑：节流 / 清理 ────────────────────────────────────────────────────


def test_is_throttled_no_record() -> None:
    assert _service().is_throttled("qq") is False


def test_is_throttled_within_window() -> None:
    svc = _service(interval=300)
    svc._last_collected["qq"] = datetime.now(UTC)
    assert svc.is_throttled("qq") is True


def test_is_throttled_expired() -> None:
    svc = _service(interval=300)
    svc._last_collected["qq"] = datetime.now(UTC) - timedelta(seconds=301)
    assert svc.is_throttled("qq") is False


def test_prune_runtime_clears_locks_and_last_collected() -> None:
    svc = _service()
    svc._last_collected["qq"] = datetime.now(UTC)
    svc._locks["qq"] = asyncio.Lock()
    svc._locks["gone"] = asyncio.Lock()
    svc.prune_runtime({"qq"})
    assert "qq" in svc._locks and "gone" not in svc._locks
    assert "qq" in svc._last_collected


async def test_list_packages() -> None:
    assert await _service().list_packages() == ["qq"]


# ── get_info（纯读）────────────────────────────────────────────────────────


async def test_get_info_not_found() -> None:
    with pytest.raises(PackageNotFoundError):
        await _service().get_info("nope")


async def test_get_info_pure_read_no_fetch(db, make_package) -> None:
    """命中 DB 快照时不触网（fetcher 调用为 0）"""
    pkg = await make_package()
    v = await PackageVersion.create(
        package=pkg, version="1.0", urls='{"x86_64":"https://x/a"}', status="success"
    )
    await PackageHash.create(
        version=v, arch="x86_64", algorithm="b2", hash_value="abc", status="success"
    )
    svc = _service(text="should-not-be-used")
    info = await svc.get_info("qq", "b2")
    assert info.version == "1.0" and info.hashes["x86_64"] == "abc"
    assert cast(FakeFetcher, svc.fetcher).text_calls == 0


async def test_get_info_data_not_ready_when_no_snapshot(db, make_package) -> None:
    await make_package()
    with pytest.raises(DataNotReadyError):
        await _service().get_info("qq", "b2")


# ── collect（采集）─────────────────────────────────────────────────────────


async def test_collect_success_persists_version_and_hashes(db, make_package) -> None:
    pkg = await make_package()
    svc = _service(text="cfg", hashes={"x86_64": "h1", "aarch64": "h2"})
    info = await svc.collect("qq")
    assert info.version == "1.2.3"
    assert info.hashes == {"x86_64": "h1", "aarch64": "h2"}

    v: PackageVersion = await PackageVersion.get(package=pkg, status="success")
    assert v.version == "1.2.3"
    hs = await PackageHash.filter(version=v)
    assert {h.arch: h.hash_value for h in hs} == {"x86_64": "h1", "aarch64": "h2"}
    assert all(h.status == "success" for h in hs)


async def test_collect_version_survives_full_hash_failure(db, make_package) -> None:
    """核心回归：version 成功但全部架构 hash 下载失败 → version 仍落库且可读"""
    pkg = await make_package()
    svc = _service(text="cfg", hashes={})  # 所有架构 hash 缺失 → None
    info = await svc.collect("qq")
    assert info.version == "1.2.3"  # version 仍在
    assert info.hashes == {"x86_64": None, "aarch64": None}

    v: PackageVersion = await PackageVersion.get(package=pkg, status="success")
    hs = await PackageHash.filter(version=v)
    assert all(h.status == "failed" and h.hash_value is None for h in hs)

    # 纯读路径也能读到 version（不被 hash 失败连坐）
    read = await svc.get_info("qq", "b2")
    assert read.version == "1.2.3"


async def test_collect_always_redownloads_hash(db, make_package) -> None:
    """每次 collect 都重新下载算 hash（无短路），即便 version 不变"""
    await make_package()
    svc = _service(text="cfg", hashes={"x86_64": "h1", "aarch64": "h2"})
    fetcher = cast(FakeFetcher, svc.fetcher)
    await svc.collect("qq")
    first_hash_calls = fetcher.hash_calls
    await svc.collect("qq")  # version 不变也应重算
    assert fetcher.hash_calls == first_hash_calls + 1
    # 两次各产出一条 success version 快照（历史保留）
    assert await PackageVersion.filter(status="success").count() == 2


async def test_collect_version_fetch_failure_records_and_raises(
    db, make_package
) -> None:
    """版本源抓取失败 → 落 failed 审计行并抛 RuntimeError（refresh → 502）"""
    pkg = await make_package()
    svc = _service(text=None)
    with pytest.raises(RuntimeError):
        await svc.collect("qq")
    v: PackageVersion = await PackageVersion.get(package=pkg)
    assert v.status == "failed" and v.version is None


async def test_collect_computes_all_algorithms(db, make_package) -> None:
    """采集单流计算全部算法：GET 任意 algorithm 均命中，不再依赖包配置算法"""
    pkg = await make_package()
    svc = _service(text="cfg", hashes={"x86_64": "h1", "aarch64": "h2"})
    await svc.collect("qq")

    v: PackageVersion = await PackageVersion.get(package=pkg, status="success")
    # 三种算法 × 两架构 = 6 行
    assert await PackageHash.filter(version=v).count() == 6
    for algo in ("b2", "sha256", "sha512"):
        rows = await PackageHash.filter(version=v, algorithm=algo)
        assert {h.arch: h.hash_value for h in rows} == {
            "x86_64": "h1",
            "aarch64": "h2",
        }

    # 请求非默认算法也能取到（核心回归：修复「请求非配置算法→hash 永远空」）
    info = await svc.get_info("qq", hash_algorithm="sha512")
    assert info.hashes == {"x86_64": "h1", "aarch64": "h2"}


# ── collect_now（手动刷新 + 节流）──────────────────────────────────────────


async def test_collect_now_throttled(db, make_package) -> None:
    await make_package()
    svc = _service(text="cfg", hashes={"x86_64": "h1"}, interval=300)
    await svc.collect_now("qq")
    with pytest.raises(CollectThrottledError):
        await svc.collect_now("qq")  # 节流窗口内再刷新


# ── 后台异步刷新 ───────────────────────────────────────────────────────────


async def test_get_info_stale_triggers_background_refresh(db, make_package) -> None:
    """stale 读取触发后台采集，且不阻塞当前响应"""
    pkg = await make_package()
    v = await PackageVersion.create(
        package=pkg, version="1.0", urls='{"x86_64":"https://x/a"}', status="success"
    )
    # 拨旧到 stale 窗口之外
    await PackageVersion.filter(id=v.id).update(
        fetched_at=datetime.now(UTC) - timedelta(seconds=9999)
    )
    svc = _service(text="cfg", hashes={"x86_64": "NEW"}, stale_seconds=60)
    fetcher = cast(FakeFetcher, svc.fetcher)

    info = await svc.get_info("qq", "b2")  # 立即返回 stale，不等下载
    assert info.version == "1.0"  # 旧值
    assert fetcher.text_calls == 0  # 当前同步路径未触网

    # 等待后台任务完成
    if svc._bg_tasks:
        await asyncio.gather(*svc._bg_tasks)
    assert fetcher.text_calls == 1  # 后台已刷新
    # 新的 success 快照已落库
    assert await PackageVersion.filter(status="success").count() == 2


async def test_get_info_fresh_does_not_trigger_refresh(db, make_package) -> None:
    pkg = await make_package()
    v = await PackageVersion.create(
        package=pkg, version="1.0", urls='{"x86_64":"https://x/a"}', status="success"
    )
    await PackageHash.create(
        version=v, arch="x86_64", algorithm="b2", hash_value="abc", status="success"
    )
    svc = _service(text="cfg", stale_seconds=3600)
    await svc.get_info("qq", "b2")
    assert len(svc._bg_tasks) == 0  # 新鲜，不触发后台刷新


async def test_concurrent_stale_gets_dedupe_single_background_collect(
    db, make_package
) -> None:
    """N 个并发 stale GET 只触发一次后台采集，不重复下载（防回归）"""
    pkg = await make_package()
    v = await PackageVersion.create(
        package=pkg, version="1.0", urls='{"x86_64":"https://x/a"}', status="success"
    )
    await PackageVersion.filter(id=v.id).update(
        fetched_at=datetime.now(UTC) - timedelta(seconds=9999)
    )
    svc = _service(text="cfg", hashes={"x86_64": "NEW"}, stale_seconds=60)
    fetcher = cast(FakeFetcher, svc.fetcher)

    # 5 个并发 stale 读：均立即返回，不应各自起后台任务
    await asyncio.gather(*[svc.get_info("qq", "b2") for _ in range(5)])
    assert len(svc._bg_tasks) == 1  # 去重：仅一个后台采集
    await asyncio.gather(*svc._bg_tasks)
    assert fetcher.text_calls == 1  # 只下载一次


async def test_get_info_urls_aligns_with_current_archs(db, make_package) -> None:
    """reload 收缩 archs 后，urls 不泄露被删架构，且与 hashes 键集一致"""
    pkg = await make_package()
    v = await PackageVersion.create(
        package=pkg,
        version="1.0",
        urls='{"x86_64":"https://x/a","aarch64":"https://x/b"}',  # 落库时含两架构
        status="success",
    )
    await PackageHash.create(
        version=v, arch="x86_64", algorithm="b2", hash_value="h", status="success"
    )
    # 当前 registry 仅 x86_64（模拟 reload 后 archs 收缩）
    svc = PackageService(
        FakeFetcher().as_fetcher(),
        make_qq_registry([ArchEnum.X86_64], version="1.0"),
        version_stale_seconds=0,
    )
    info = await svc.get_info("qq", "b2")
    assert info.urls == {"x86_64": "https://x/a"}  # aarch64 不再泄露
    assert set(info.urls) == set(info.hashes) == {"x86_64"}
