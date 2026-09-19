"""PackageService 安装包路径版本域集成测试（DebParser + Fake 桩）。

覆盖 collect_version 的 ``PackageFileVersionParser`` 分支：
- 静态 URL（DebParser）：不取版本源响应，头部提取版本 + hash 正常落库
- 动态 URL（版本源响应定位）：fetch_text 仍发生
- 失败路径：头部下载失败 / 结构不符 / 各架构版本不一致 / URL 全缺 → failed 审计行
"""

from __future__ import annotations

import json
from typing import Any, cast

import pytest

from app.constants import ArchEnum
from app.models import Package, PackageHash, PackageVersion
from app.parsers.deb import DebControlVersionMixin, DebParser
from app.registry import PackageEntry, PackageRegistry
from app.services.package_service import PackageService
from tests.fakes import FakeFetcher, build_deb

_DEB_HEAD: bytes = build_deb(version="2.0.0-100")
_DEB_URLS: dict[str, str] = {
    "x86_64": "https://x/app_amd64.deb",
    "aarch64": "https://x/app_arm64.deb",
}


class _DynamicDebParser(DebControlVersionMixin):
    """动态定位安装包 URL 的桩（模拟 QQ 形态：URL 来自版本源响应）"""

    def parse_url(self, arch: ArchEnum | str, response_data: str) -> str | None:
        return json.loads(response_data).get(self._arch_value(arch))


def _registry(
    parser: DebControlVersionMixin,
    archs: list[ArchEnum] | None = None,
) -> PackageRegistry:
    entry = PackageEntry(
        name="app",
        parser=parser,
        fetch_url="https://x/cfg.json",
        archs=archs or [ArchEnum.X86_64, ArchEnum.AARCH64],
    )
    reg = PackageRegistry()
    reg.replace_all([entry])
    return reg


def _deb_service(
    head: bytes | dict[str, bytes] | None = _DEB_HEAD,
    hashes: dict[str, str | None] | None = None,
    parser: DebControlVersionMixin | None = None,
    text: str | None = None,
) -> PackageService:
    fetcher = FakeFetcher(
        text=text,
        hashes=hashes or {"x86_64": "h1", "aarch64": "h2"},
        head=head,
    )
    if parser is None:
        parser = DebParser(
            urls={"amd64": _DEB_URLS["x86_64"], "arm64": _DEB_URLS["aarch64"]}
        )
    return PackageService(fetcher.as_fetcher(), _registry(parser))


async def _make_deb_package(make_package, **overrides: Any) -> Package:
    """创建 parser_type=deb 的 packages 行（与 _deb_service 的 registry 同名）"""
    kwargs: dict[str, Any] = {
        "name": "app",
        "parser_type": "deb",
        "parser_config": json.dumps(
            {"urls": {"amd64": _DEB_URLS["x86_64"], "arm64": _DEB_URLS["aarch64"]}}
        ),
        "fetch_url": "",
    }
    kwargs.update(overrides)
    return await make_package(**kwargs)


# ── 静态 URL（DebParser）─────────────────────────────────────────────────────


async def test_collect_deb_success_persists_version_and_hashes(
    db, make_package
) -> None:
    pkg = await _make_deb_package(make_package)
    svc = _deb_service()
    info = await svc.collect("app")
    assert info.version == "2.0.0_100"
    assert info.urls == _DEB_URLS
    assert info.hashes == {"x86_64": "h1", "aarch64": "h2"}

    fetcher = cast(FakeFetcher, svc.fetcher)
    assert fetcher.text_calls == 0  # 静态 URL：版本源响应不参与
    assert fetcher.head_calls == 2  # 双架构各下载一次头部

    v: PackageVersion = await PackageVersion.get(package=pkg, status="success")
    assert v.version == "2.0.0_100"
    assert json.loads(v.urls) == _DEB_URLS
    # 三种算法 × 两架构
    assert await PackageHash.filter(version=v, status="success").count() == 6


async def test_collect_deb_head_failure_records_and_raises(db, make_package) -> None:
    """头部下载失败 → failed 审计行 + RuntimeError"""
    pkg = await _make_deb_package(make_package)
    with pytest.raises(RuntimeError):
        await _deb_service(head=None).collect("app")
    v: PackageVersion = await PackageVersion.get(package=pkg)
    assert v.status == "failed" and "提取版本号" in v.error


async def test_collect_deb_bad_structure_records_and_raises(db, make_package) -> None:
    """头部非 deb 结构 → 版本提取失败 → failed 审计行"""
    pkg = await _make_deb_package(make_package)
    with pytest.raises(RuntimeError):
        await _deb_service(head=b"garbage not a deb").collect("app")
    v: PackageVersion = await PackageVersion.get(package=pkg)
    assert v.status == "failed" and v.version is None


async def test_collect_deb_cross_arch_version_mismatch(db, make_package) -> None:
    """各架构安装包版本不一致 → 整体拒绝（防部分发布挂错版本号）"""
    pkg = await _make_deb_package(make_package)
    heads = {
        _DEB_URLS["x86_64"]: build_deb(version="2.0.0-100"),
        _DEB_URLS["aarch64"]: build_deb(version="2.0.0-99"),
    }
    with pytest.raises(RuntimeError):
        await _deb_service(head=heads).collect("app")
    v: PackageVersion = await PackageVersion.get(package=pkg)
    assert v.status == "failed" and "版本不一致" in v.error


async def test_collect_deb_partial_arch_urls_still_succeeds(db, make_package) -> None:
    """仅部分架构配置了 URL → 可用架构照常落库，缺失架构 hash 行失败"""
    pkg = await _make_deb_package(make_package)
    svc = _deb_service(parser=DebParser(urls={"amd64": _DEB_URLS["x86_64"]}))
    info = await svc.collect("app")
    assert info.version == "2.0.0_100"
    assert info.urls == {"x86_64": _DEB_URLS["x86_64"]}

    v: PackageVersion = await PackageVersion.get(package=pkg, status="success")
    rows = await PackageHash.filter(version=v)
    failed_archs = {h.arch for h in rows if h.status == "failed"}
    assert failed_archs == {"aarch64"}  # 缺 URL 架构 hash 落失败行


async def test_collect_deb_version_survives_hash_failure(db, make_package) -> None:
    """安装包路径同样满足核心回归：version 先行落库，hash 全失败不连坐"""
    pkg = await _make_deb_package(make_package)
    info = await _deb_service(hashes={"x86_64": None, "aarch64": None}).collect("app")
    assert info.version == "2.0.0_100"
    assert info.hashes == {"x86_64": None, "aarch64": None}
    assert await PackageVersion.get(package=pkg, status="success") is not None


async def test_collect_deb_partial_head_failure_still_succeeds(
    db, make_package
) -> None:
    """单架构头部下载失败仅跳过该架构，其余照常落库（不连坐）"""
    pkg = await _make_deb_package(make_package)
    # head 按 URL 精确匹配：aarch64 缺失 → 该架构跳过，x86_64 照常提取
    svc = _deb_service(head={_DEB_URLS["x86_64"]: _DEB_HEAD})
    info = await svc.collect("app")
    assert info.version == "2.0.0_100"
    assert info.urls == _DEB_URLS  # URL 已定位，仅版本提取跳过

    v: PackageVersion = await PackageVersion.get(package=pkg, status="success")
    assert v.version == "2.0.0_100"


async def test_collect_deb_resolve_raw_url_exception_swallowed(
    db, make_package
) -> None:
    """resolve_raw_url 抛异常（如签名故障）→ 逐架构拦下，走版本失败落库而非逃逸"""

    class _RaisingResolveParser(DebParser):
        async def resolve_raw_url(self, arch, raw_url: str) -> str | None:
            raise RuntimeError("签名服务故障")

    pkg = await _make_deb_package(make_package)
    raising_parser = _RaisingResolveParser(
        urls={"amd64": _DEB_URLS["x86_64"], "arm64": _DEB_URLS["aarch64"]}
    )
    with pytest.raises(RuntimeError, match="采集 app 版本失败"):
        await _deb_service(parser=raising_parser).collect("app")
    v: PackageVersion = await PackageVersion.get(package=pkg)
    assert v.status == "failed" and "提取版本号" in v.error


# ── 动态 URL（版本源响应定位，QQ 形态）──────────────────────────────────────


async def test_collect_deb_dynamic_urls_fetch_text_once(db, make_package) -> None:
    """无静态配置：先取版本源响应定位 URL，再逐架构下载头部"""
    pkg = await _make_deb_package(make_package, parser_config=None)
    svc = PackageService(
        FakeFetcher(
            text=json.dumps(_DEB_URLS),
            hashes={"x86_64": "h1", "aarch64": "h2"},
            head=_DEB_HEAD,
        ).as_fetcher(),
        _registry(_DynamicDebParser()),
    )
    info = await svc.collect("app")
    assert info.version == "2.0.0_100"

    fetcher = cast(FakeFetcher, svc.fetcher)
    assert fetcher.text_calls == 1
    assert fetcher.head_calls == 2
    v: PackageVersion = await PackageVersion.get(package=pkg, status="success")
    assert json.loads(v.urls) == _DEB_URLS


async def test_collect_deb_dynamic_url_source_failure(db, make_package) -> None:
    """动态定位时版本源抓取失败 → failed 审计行且不下载头部"""
    pkg = await _make_deb_package(make_package, parser_config=None)
    svc = PackageService(
        FakeFetcher(text=None, head=_DEB_HEAD).as_fetcher(),
        _registry(_DynamicDebParser()),
    )
    with pytest.raises(RuntimeError):
        await svc.collect("app")
    v: PackageVersion = await PackageVersion.get(package=pkg)
    assert v.status == "failed" and "无法获取版本源" in v.error
    assert cast(FakeFetcher, svc.fetcher).head_calls == 0
