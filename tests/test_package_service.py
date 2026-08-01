"""app.services.package_service 集成测试（DB + Fake 桩）。

覆盖：节流判断、_try_cache 各分支、persist_result 落库与状态判定、
persist_failure 兜底、get_info_cached 的命中/回源/节流降级/拒绝路径。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast
from unittest.mock import patch

import pytest

from app.constants import ArchEnum
from app.models import PackageHash, PackageVersion
from app.schemas import PackageInfo
from app.services.package_service import (
    CollectThrottledError,
    PackageNotFoundError,
    PackageService,
)
from tests.fakes import FakeFetcher, make_qq_registry


def _service(
    text: str = "", hashes: dict[str, str | None] | None = None, interval: int = 0
) -> PackageService:
    """构造一个指向单包 'qq'（双架构）registry 的 PackageService。"""
    return PackageService(
        FakeFetcher(text=text, hashes=hashes).as_fetcher(),
        make_qq_registry([ArchEnum.X86_64, ArchEnum.AARCH64], version="1.2.3"),
        interval,
    )


def _info(
    version: str = "1.2.3",
    hashes: dict[str, str | None] | None = None,
    urls: dict[str, str] | None = None,
) -> PackageInfo:
    return PackageInfo(
        name="qq",
        version=version,
        urls=urls or {"x86_64": "https://x/amd64.deb"},
        hashes=hashes if hashes is not None else {"x86_64": "deadbeef"},
    )


# ── 纯逻辑：节流 / 清理 ────────────────────────────────────────────────────


def test_is_throttled_no_record() -> None:
    svc = _service()
    assert svc.is_throttled("qq") is False


def test_is_throttled_within_window() -> None:
    svc = _service(interval=300)
    svc._last_collected["qq"] = datetime.now(UTC)
    assert svc.is_throttled("qq") is True


def test_is_throttled_expired() -> None:
    svc = _service(interval=300)
    svc._last_collected["qq"] = datetime.now(UTC) - timedelta(seconds=301)
    assert svc.is_throttled("qq") is False


def test_prune_last_collected_keeps_only_named() -> None:
    svc = _service()
    svc._last_collected["qq"] = datetime.now(UTC)
    svc._last_collected["gone"] = datetime.now(UTC)
    svc.prune_last_collected({"qq"})
    assert "qq" in svc._last_collected
    assert "gone" not in svc._last_collected


async def test_list_packages() -> None:
    svc = _service()
    assert await svc.list_packages() == ["qq"]


# ── get_info 编排 ────────────────────────────────────────────────────────────


async def test_get_info_not_found() -> None:
    svc = _service()
    with pytest.raises(PackageNotFoundError):
        await svc.get_info("nope")


async def test_get_info_success_sets_last_collected() -> None:
    svc = _service(
        text="cfg",
        hashes={"x86_64": "h1", "aarch64": "h2"},
    )
    info = await svc.get_info("qq")
    assert info.version == "1.2.3"
    assert info.hashes == {"x86_64": "h1", "aarch64": "h2"}
    # 采集完成时间被记录 → 后续节流生效
    assert "qq" in svc._last_collected


async def test_get_info_partial_when_hash_missing() -> None:
    """resolve_url 仍返回 URL 但 fetcher 缺某架构 hash → 该架构为 None"""
    svc = _service(text="cfg", hashes={"x86_64": "h1"})  # aarch64 缺失 → None
    info = await svc.get_info("qq")
    assert info.hashes["x86_64"] == "h1"
    assert info.hashes["aarch64"] is None


# ── _try_cache（DB）──────────────────────────────────────────────────────────


async def test_try_cache_no_package(db, make_package) -> None:
    svc = _service()
    assert await svc._try_cache("qq", "b2", 60) is None


async def test_try_cache_no_version(db, make_package) -> None:
    await make_package()
    svc = _service()
    assert await svc._try_cache("qq", "b2", 60) is None


async def test_try_cache_fresh_hit(db, make_package) -> None:
    pkg = await make_package()
    v = await PackageVersion.create(package=pkg, version="1.0", status="success")
    await PackageHash.create(version=v, arch="x86_64", algorithm="b2", hash_value="abc")
    svc = _service()
    info = await svc._try_cache("qq", "b2", 3600)
    assert (
        info is not None and info.version == "1.0" and info.hashes == {"x86_64": "abc"}
    )


async def test_try_cache_expired_returns_none(db, make_package) -> None:
    pkg = await make_package()
    v = await PackageVersion.create(package=pkg, version="1.0", status="success")
    await PackageHash.create(version=v, arch="x86_64", algorithm="b2", hash_value="abc")
    # 把 fetched_at 拨旧到 TTL 之外
    await PackageVersion.filter(id=v.id).update(
        fetched_at=datetime.now(UTC) - timedelta(seconds=9999)
    )
    svc = _service()
    assert await svc._try_cache("qq", "b2", 60) is None


async def test_try_cache_stale_ignores_age(db, make_package) -> None:
    """max_age=None 时忽略年龄（节流降级路径）"""
    pkg = await make_package()
    v = await PackageVersion.create(package=pkg, version="1.0", status="success")
    await PackageHash.create(version=v, arch="x86_64", algorithm="b2", hash_value="abc")
    await PackageVersion.filter(id=v.id).update(
        fetched_at=datetime.now(UTC) - timedelta(seconds=9999)
    )
    svc = _service()
    info = await svc._try_cache("qq", "b2", None)
    assert info is not None and info.version == "1.0"


async def test_try_cache_wrong_algorithm_returns_none(db, make_package) -> None:
    """快照只有 b2，请求 sha256 → None → 触发回源"""
    pkg = await make_package()
    v = await PackageVersion.create(package=pkg, version="1.0", status="success")
    await PackageHash.create(version=v, arch="x86_64", algorithm="b2", hash_value="abc")
    svc = _service()
    assert await svc._try_cache("qq", "sha256", 3600) is None


# ── persist_result / persist_failure（DB）────────────────────────────────────


async def test_persist_result_success(db, make_package) -> None:
    pkg = await make_package()
    svc = _service()
    await svc.persist_result(pkg, _info(hashes={"x86_64": "h1"}), algorithm="b2")
    v = await PackageVersion.get(package=pkg)
    assert v.status == "success"
    hs = await PackageHash.filter(version=v)
    assert {h.arch: h.hash_value for h in hs} == {"x86_64": "h1"}


async def test_persist_result_partial_when_none_hash(db, make_package) -> None:
    pkg = await make_package()
    svc = _service()
    await svc.persist_result(
        pkg,
        _info(hashes={"x86_64": "h1", "aarch64": None}),
        algorithm="b2",
    )
    v = await PackageVersion.get(package=pkg)
    assert v.status == "partial"


async def test_persist_result_no_version_records_failure(db, make_package) -> None:
    pkg = await make_package()
    svc = _service()
    await svc.persist_result(pkg, _info(version=""), algorithm="b2")
    v = await PackageVersion.get(package=pkg)
    assert v.status == "failed" and v.version is None


async def test_persist_result_all_none_hashes_records_failure(db, make_package) -> None:
    pkg = await make_package()
    svc = _service()
    await svc.persist_result(
        pkg, _info(hashes={"x86_64": None, "aarch64": None}), algorithm="b2"
    )
    v = await PackageVersion.get(package=pkg)
    assert v.status == "failed"


async def test_persist_result_atomic_rollback(db, make_package) -> None:
    """version+hashes 单事务：hashes 写入失败时 version 也回滚（不留不完整快照）"""
    pkg = await make_package()
    svc = _service()

    async def _boom(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("db write failed")

    with patch.object(PackageHash, "bulk_create", _boom), pytest.raises(RuntimeError):
        await svc.persist_result(pkg, _info(hashes={"x86_64": "h1"}), algorithm="b2")
    # version 未残留
    assert await PackageVersion.filter(package=pkg).count() == 0


async def test_persist_failure_swallows_db_error(db, make_package) -> None:
    """persist_failure 自身落库异常被吞掉，不再上抛（兜底契约）"""
    pkg = await make_package()
    svc = _service()

    async def _boom(*a: Any, **k: Any) -> Any:
        raise RuntimeError("db down")

    with patch.object(PackageVersion, "create", _boom):
        await svc.persist_failure(pkg, "boom")  # 不应抛
    assert await PackageVersion.filter(package=pkg).count() == 0


# ── get_info_cached 各路径（DB）──────────────────────────────────────────────


async def test_cached_fresh_hit_no_fetch(db, make_package) -> None:
    pkg = await make_package()
    v = await PackageVersion.create(package=pkg, version="1.0", status="success")
    await PackageHash.create(version=v, arch="x86_64", algorithm="b2", hash_value="abc")
    svc = _service(text="should-not-be-used")
    info = await svc.get_info_cached("qq", "b2", max_age_seconds=3600)
    assert info.version == "1.0"
    assert cast(FakeFetcher, svc.fetcher).text_calls == 0  # 命中缓存，未回源


async def test_cached_miss_persists_and_serves(db, make_package) -> None:
    """回源后落库：第二次请求命中新鲜快照而非被节流拒绝"""
    await make_package()
    svc = _service(text="cfg", hashes={"x86_64": "h1"}, interval=300)
    fetcher = cast(FakeFetcher, svc.fetcher)
    info1 = await svc.get_info_cached("qq", "b2", max_age_seconds=60)
    assert info1.hashes == {"x86_64": "h1", "aarch64": None}
    # 回源已落库
    assert await PackageVersion.filter(status__in=["success", "partial"]).count() == 1
    # 节流窗口内第二次请求 → 命中新鲜快照（不再回源、不 429）
    fetcher.text_calls = 0
    info2 = await svc.get_info_cached("qq", "b2", max_age_seconds=60)
    assert info2.hashes == {"x86_64": "h1", "aarch64": None}
    assert fetcher.text_calls == 0


async def test_cached_throttled_degrades_to_stale(db, make_package) -> None:
    """节流内且有过期 stale → 降级返回 stale 而非 429"""
    pkg = await make_package()
    v = await PackageVersion.create(package=pkg, version="1.0", status="success")
    await PackageHash.create(version=v, arch="x86_64", algorithm="b2", hash_value="abc")
    await PackageVersion.filter(id=v.id).update(
        fetched_at=datetime.now(UTC) - timedelta(seconds=9999)
    )
    svc = _service(text="cfg", hashes={"x86_64": "NEW"}, interval=300)
    svc._last_collected["qq"] = datetime.now(UTC)  # 强制节流
    info = await svc.get_info_cached("qq", "b2", max_age_seconds=60)
    assert info.version == "1.0" and info.hashes == {"x86_64": "abc"}  # stale


async def test_cached_throttled_no_stale_raises_429(db, make_package) -> None:
    """节流内且无任何 stale（变换 algorithm 绕过）→ CollectThrottledError"""
    await make_package()
    svc = _service(text="cfg", hashes={"x86_64": "h1"}, interval=300)
    svc._last_collected["qq"] = datetime.now(UTC)
    with pytest.raises(CollectThrottledError):
        await svc.get_info_cached("qq", "sha256", max_age_seconds=60)
