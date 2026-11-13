"""aur_metadata.services.package_service 集成测试（DB + Fake 桩）。

覆盖版本服务的契约：
- 节流 / 运行时清理（纯逻辑）
- get_info 纯 DB 读、不触发采集；download_urls 实时签名生成，失败降级 None
- 无快照 → DataNotReadyError
- collect_version：版本落库；版本未变复用现有行，不膨胀历史
- 版本抓取失败 → 落 failed 行并抛 RuntimeError
- collect_version_now 节流 → CollectThrottledError；采集路径不生成 download_urls
"""


import asyncio
from datetime import UTC, datetime, timedelta
from typing import cast

import pytest

from aur_metadata.constants import ArchEnum
from aur_metadata.models import PackageVersion
from aur_metadata.services.package_service import (
    CollectThrottledError,
    DataNotReadyError,
    PackageNotFoundError,
    PackageService,
)
from tests.fakes import FakeFetcher, make_qq_registry


def _service(
    text: str | None = "",
    interval: int = 0,
    signed_by_arch: dict[str, str] | None = None,
    raise_on_resolve: bool = False,
) -> PackageService:
    """构造一个指向单包 'qq'（双架构）registry 的 PackageService。"""
    return PackageService(
        FakeFetcher(text=text).as_fetcher(),
        make_qq_registry(
            [ArchEnum.X86_64, ArchEnum.AARCH64],
            version="1.2.3",
            signed_by_arch=signed_by_arch,
            raise_on_resolve=raise_on_resolve,
        ),
        min_collect_interval_seconds=interval,
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
    """命中 DB 快照时不触网（fetcher 调用为 0）；恒等解析器 download_urls==urls"""
    pkg = await make_package()
    await PackageVersion.create(
        package=pkg, version="1.0", urls='{"x86_64":"https://x/a"}', status="success"
    )
    svc = _service(text="should-not-be-used")
    info = await svc.get_info("qq")
    assert info.version == "1.0"
    assert info.download_urls == info.urls  # 恒等解析器：实时链接与原始链接相同
    assert cast(FakeFetcher, svc.fetcher).text_calls == 0


async def test_get_info_data_not_ready_when_no_snapshot(db, make_package) -> None:
    """无快照直接 503，不隐式触发采集"""
    await make_package()
    svc = _service()
    with pytest.raises(DataNotReadyError):
        await svc.get_info("qq")
    assert cast(FakeFetcher, svc.fetcher).text_calls == 0


# ── get_info download_urls（实时签名链接）──────────────────────────────────


async def test_get_info_populates_download_urls(db, make_package) -> None:
    """签名解析器：download_urls 逐架构实时生成，键集与 urls 对齐"""
    pkg = await make_package()
    await PackageVersion.create(
        package=pkg,
        version="1.0",
        urls='{"x86_64":"https://x/a","aarch64":"https://x/b"}',
        status="success",
    )
    svc = _service(
        text="should-not-be-used",
        signed_by_arch={"x86_64": "https://signed/a", "aarch64": "https://signed/b"},
    )
    info = await svc.get_info("qq")
    assert info.urls == {"x86_64": "https://x/a", "aarch64": "https://x/b"}
    assert info.download_urls == {
        "x86_64": "https://signed/a",
        "aarch64": "https://signed/b",
    }
    # 签名是 parser 内部 RPC，不经过 fetcher（不下载安装包体）
    assert cast(FakeFetcher, svc.fetcher).text_calls == 0


async def test_get_info_download_url_sign_failure_degrades_to_none(
    db, make_package,
) -> None:
    """单架构签名失败 → 该架构 download_urls 为 None，响应整体不受影响"""
    pkg = await make_package()
    await PackageVersion.create(
        package=pkg,
        version="1.0",
        urls='{"x86_64":"https://x/a","aarch64":"https://x/b"}',
        status="success",
    )
    # aarch64 无签名映射 → 模拟该架构签名失败
    svc = _service(signed_by_arch={"x86_64": "https://signed/a"})
    info = await svc.get_info("qq")
    assert info.download_urls == {"x86_64": "https://signed/a", "aarch64": None}
    assert info.version == "1.0"


async def test_get_info_download_url_exception_degrades_to_none(
    db, make_package,
) -> None:
    """resolve_raw_url 抛异常被服务层吞掉 → 置 None，不拖垮查询响应"""
    pkg = await make_package()
    await PackageVersion.create(
        package=pkg,
        version="1.0",
        urls='{"x86_64":"https://x/a","aarch64":"https://x/b"}',
        status="success",
    )
    svc = _service(raise_on_resolve=True)
    info = await svc.get_info("qq")
    assert info.download_urls == {"x86_64": None, "aarch64": None}
    assert info.version == "1.0"


# ── collect_version（采集）─────────────────────────────────────────────────


async def test_collect_version_persists_snapshot(db, make_package) -> None:
    pkg = await make_package()
    svc = _service(text="cfg")
    info = await svc.collect_version("qq")
    assert info.version == "1.2.3"
    assert info.urls

    v: PackageVersion = await PackageVersion.get(package=pkg, status="success")
    assert v.version == "1.2.3"


async def test_collect_version_same_version_reuses_row(db, make_package) -> None:
    """版本未变时复用现有 success 行，只刷新 urls/fetched_at，不膨胀历史"""
    pkg = await make_package()
    svc = _service(text="cfg")
    first = await svc.collect_version("qq")
    row_before: PackageVersion = await PackageVersion.get(
        package=pkg, status="success"
    )
    fetched_before = row_before.fetched_at

    second = await svc.collect_version("qq")
    assert second.version == first.version == "1.2.3"
    assert await PackageVersion.filter(status="success").count() == 1
    row_after: PackageVersion = await PackageVersion.get(
        package=pkg, status="success"
    )
    assert row_after.id == row_before.id
    assert row_after.fetched_at > fetched_before


async def test_collect_version_new_version_inserts_row(db, make_package) -> None:
    """版本变化时插入新行，历史保留"""
    pkg = await make_package()
    await PackageVersion.create(
        package=pkg, version="1.0.0", urls="{}", status="success"
    )
    svc = _service(text="cfg")
    await svc.collect_version("qq")
    assert await PackageVersion.filter(status="success").count() == 2


async def test_collect_version_fetch_failure_records_and_raises(
    db, make_package
) -> None:
    """版本源抓取失败 → 落 failed 审计行并抛 RuntimeError（refresh → 502）"""
    pkg = await make_package()
    svc = _service(text=None)
    with pytest.raises(RuntimeError):
        await svc.collect_version("qq")
    v: PackageVersion = await PackageVersion.get(package=pkg)
    assert v.status == "failed" and v.version is None


async def test_collect_version_parse_failure_records(db, make_package) -> None:
    """版本号解析失败 → failed 审计行"""
    await make_package()
    svc = PackageService(
        FakeFetcher(text="cfg").as_fetcher(),
        make_qq_registry([ArchEnum.X86_64], version=None),
    )
    with pytest.raises(RuntimeError):
        await svc.collect_version("qq")
    v: PackageVersion = await PackageVersion.get(status="failed")
    assert "无法解析版本号" in (v.error or "")


# ── collect_version_now（手动刷新 + 节流）──────────────────────────────────


async def test_collect_version_now_throttled(db, make_package) -> None:
    await make_package()
    svc = _service(text="cfg", interval=300)
    await svc.collect_version_now("qq")
    with pytest.raises(CollectThrottledError):
        await svc.collect_version_now("qq")  # 节流窗口内再刷新


async def test_collect_version_now_info_has_empty_download_urls(
    db, make_package,
) -> None:
    """采集路径不生成 download_urls（read-path-only），refresh 响应字段为空 dict"""
    await make_package()
    svc = _service(text="cfg", signed_by_arch={"x86_64": "https://signed/a"})
    info = await svc.collect_version_now("qq")
    assert info.version == "1.2.3"
    assert info.download_urls == {}


async def test_collect_version_now_unknown_package() -> None:
    with pytest.raises(PackageNotFoundError):
        await _service().collect_version_now("ghost")


async def test_get_info_urls_aligns_with_current_archs(db, make_package) -> None:
    """reload 收缩 archs 后，urls 不泄露被删架构"""
    pkg = await make_package()
    await PackageVersion.create(
        package=pkg,
        version="1.0",
        urls='{"x86_64":"https://x/a","aarch64":"https://x/b"}',  # 落库时含两架构
        status="success",
    )
    # 当前 registry 仅 x86_64（模拟 reload 后 archs 收缩）
    svc = PackageService(
        FakeFetcher().as_fetcher(),
        make_qq_registry([ArchEnum.X86_64], version="1.0"),
    )
    info = await svc.get_info("qq")
    assert info.urls == {"x86_64": "https://x/a"}  # aarch64 不再泄露
