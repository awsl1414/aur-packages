"""包采集编排服务。

版本采集与 hash 下载是两个独立域：各自独立 fetch、独立事务落库。version 先行落库，
永不被 hash 下载失败回滚；查询接口（get_info）纯读 DB，永不下载，stale 时仅
fire-and-forget 触发后台刷新。每次 collect 都重新下载算 hash（无短路）。
"""

import asyncio
import json
import logging
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from tortoise.transactions import in_transaction

from app.constants import ArchEnum, HashAlgorithmEnum
from app.fetcher import Fetcher
from app.models import Package, PackageHash, PackageVersion
from app.parsers.base import BaseParser, PackageFileVersionParser
from app.registry import PackageEntry, PackageRegistry
from app.schemas import PackageInfo

logger = logging.getLogger(__name__)

# hash 行失败原因（区分两阶段）
_ERR_NO_DOWNLOAD_URL = "无法获取可下载 URL"
_ERR_HASH_FAILED = "下载或 hash 计算失败"

# 采集时一次性计算全部支持的算法（单流多 hash），使 GET 任意 algorithm 都能命中
_ALL_ALGORITHMS: list[str] = [a.value for a in HashAlgorithmEnum]
# 采集后回读 / refresh 返回时默认使用的算法
_DEFAULT_ALGORITHM: str = HashAlgorithmEnum.B2.value


class PackageNotFoundError(KeyError):
    """请求的包未在注册表中"""


class CollectThrottledError(Exception):
    """包采集触发节流（两次采集间隔小于 min_collect_interval_seconds）"""


class DataNotReadyError(Exception):
    """包已注册但尚无任何成功版本快照可读"""


@dataclass
class _VersionSnapshot:
    """版本采集结果：已落库的 version 行 + 解析出的版本号与各架构原始 URL"""

    version_row: PackageVersion
    version: str
    urls: dict[str, str]


@dataclass
class _HashResult:
    """单架构 × 单算法 hash 采集结果（含失败原因，便于逐行落库）"""

    arch_value: str
    algorithm: str
    hash_value: str | None
    url: str | None
    error: str | None


def _utcnow() -> datetime:
    return datetime.now(UTC)


class PackageService:
    """编排 fetch + parse + hash 计算的采集与查询服务。

    独占采集与查询、per-package 锁与节流；调度器与手动刷新均委托本服务。
    """

    def __init__(
        self,
        fetcher: Fetcher,
        registry: PackageRegistry,
        min_collect_interval_seconds: int = 0,
        version_stale_seconds: int = 0,
    ) -> None:
        self.fetcher = fetcher
        self.registry = registry
        self._min_collect_interval = min_collect_interval_seconds
        self._version_stale_seconds = version_stale_seconds
        # per-package 采集锁：保证同包不重入（QQ 签名+下载较慢）
        self._locks: dict[str, asyncio.Lock] = {}
        # per-package 上次采集完成时间（仅内存，重启重置；节流与后台刷新共用）
        self._last_collected: dict[str, datetime] = {}
        # 后台刷新任务引用，防止被 GC 回收
        self._bg_tasks: set[asyncio.Task[None]] = set()
        # 已在排队/运行的后台采集包名，防止并发 stale GET 各起一个重复采集
        self._bg_inflight: set[str] = set()

    # ── 节流 / 运行时清理 ────────────────────────────────────────────────

    def is_throttled(self, name: str) -> bool:
        """该包是否处于采集节流窗口内（距上次采集不足最小间隔）"""
        last: datetime | None = self._last_collected.get(name)
        if last is None or self._min_collect_interval <= 0:
            return False
        return _utcnow() - last < timedelta(seconds=self._min_collect_interval)

    def prune_runtime(self, keep: set[str]) -> None:
        """剔除不在 ``keep`` 集合中的包的节流记录与采集锁。

        reload 后已删除/停用的包不再采集，其运行时状态应清理，避免长生命周期下只增不减。
        """
        self._last_collected = {
            n: t for n, t in self._last_collected.items() if n in keep
        }
        self._locks = {n: lk for n, lk in self._locks.items() if n in keep}

    # ── 查询（纯读） ────────────────────────────────────────────────────

    async def list_packages(self) -> list[str]:
        """返回所有启用（enabled）的包名"""
        return [entry.name for entry in self.registry.list_all()]

    async def get_info(
        self,
        name: str,
        hash_algorithm: str = HashAlgorithmEnum.B2.value,
    ) -> PackageInfo:
        """纯 DB 读：返回最新成功版本快照 + 其所请求算法的各架构 hash。

        无网络、不阻塞下载。version fetched_at 超过 ``version_stale_seconds``
        时 fire-and-forget 触发后台刷新；包已注册但从未采集成功则抛
        ``DataNotReadyError``（路由层转「数据未就绪」），并尝试后台首次采集。
        """
        entry: PackageEntry | None = self.registry.get(name)
        if entry is None:
            raise PackageNotFoundError(name)

        read: tuple[PackageInfo, datetime] | None = await self._read_info(
            name, hash_algorithm, entry
        )
        if read is None:
            # 无任何成功版本快照：尝试后台首次采集，并告知调用方数据未就绪
            self._maybe_trigger_refresh(name)
            raise DataNotReadyError(name)

        info, fetched_at = read
        if self._is_stale(fetched_at):
            self._maybe_trigger_refresh(name)
        return info

    async def _read_info(
        self, name: str, hash_algorithm: str, entry: PackageEntry
    ) -> tuple[PackageInfo, datetime] | None:
        """从 DB 读最新成功 version + 其 hashes；无则返回 None。

        urls 与 hashes 均以**当前** entry.archs 为键集：reload 改动 archs 后，
        落库时捕获的旧 urls 不再原样泄露（被删架构不出现，新架构无 URL 则缺），
        保证两个 dict 键集一致。
        """
        pkg: Package | None = await Package.get_or_none(name=name)
        if pkg is None:
            return None

        latest: PackageVersion | None = (
            await PackageVersion.filter(package=pkg, status="success")
            .order_by("-fetched_at", "-id")
            .first()
        )
        if latest is None or not latest.version or latest.fetched_at is None:
            return None

        persisted_urls: dict[str, str] = json.loads(latest.urls) if latest.urls else {}
        urls: dict[str, str] = {
            arch.value: persisted_urls[arch.value]
            for arch in entry.archs
            if arch.value in persisted_urls
        }
        records: list[PackageHash] = await PackageHash.filter(
            version=latest, algorithm=hash_algorithm
        )
        hashes: dict[str, str | None] = {arch.value: None for arch in entry.archs}
        for h in records:
            if h.status == "success" and h.hash_value:
                hashes[h.arch] = h.hash_value

        return (
            PackageInfo(name=name, version=latest.version, urls=urls, hashes=hashes),
            latest.fetched_at,
        )

    def _is_stale(self, fetched_at: datetime) -> bool:
        """版本快照是否超过 ``version_stale_seconds`` 视为过期"""
        if self._version_stale_seconds <= 0:
            return False
        ts: datetime = fetched_at
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        return _utcnow() - ts > timedelta(seconds=self._version_stale_seconds)

    def _maybe_trigger_refresh(self, name: str) -> None:
        """fire-and-forget 触发后台采集：节流窗口内、正采集中或已有后台任务排队时跳过。

        后台任务在下一 event-loop tick 才取锁，故并发 stale GET 会同时看到锁空闲——
        用 ``_bg_inflight`` 去重，确保同包至多一个后台采集在排队/运行，避免 N 个
        请求触发 N 次冗余全量下载。
        """
        if self.is_throttled(name) or name in self._bg_inflight:
            return
        lock: asyncio.Lock | None = self._locks.get(name)
        if lock is not None and lock.locked():
            return
        self._bg_inflight.add(name)
        task: asyncio.Task[None] = asyncio.create_task(self._background_collect(name))
        self._bg_tasks.add(task)
        task.add_done_callback(self._bg_tasks.discard)

    async def _background_collect(self, name: str) -> None:
        """后台采集回调：吞异常仅记日志，绝不影响触发它的 GET 响应"""
        try:
            await self.collect(name)
        except Exception:
            logger.exception("后台刷新 %s 失败", name)
        finally:
            self._bg_inflight.discard(name)

    # ── 采集（写） ──────────────────────────────────────────────────────

    async def collect(self, name: str) -> PackageInfo:
        """同步采集：版本→hash，回读 DB 返回 PackageInfo。

        供定时任务与后台刷新调用；手动刷新走 ``collect_now``（含节流拒绝）。
        """
        async with self._locks.setdefault(name, asyncio.Lock()):
            return await self._collect_locked(name)

    async def collect_now(self, name: str) -> PackageInfo:
        """手动触发采集：节流检查与采集同处 per-package 锁内（消除 check-then-act）。

        节流内抛 ``CollectThrottledError`` → 路由层转 429。
        """
        if self.registry.get(name) is None:
            raise PackageNotFoundError(name)
        async with self._locks.setdefault(name, asyncio.Lock()):
            if self.is_throttled(name):
                raise CollectThrottledError(name)
            return await self._collect_locked(name)

    async def _collect_locked(self, name: str) -> PackageInfo:
        """实际采集逻辑（调用方已持 per-package 锁）。

        版本域失败（已由 collect_version 落 failed 审计行）抛 RuntimeError：
        refresh 路径据此转 502；定时/后台路径各自吞掉。hash 域失败不抛——
        version 已先行落库，逐架构失败行单独记录。每次都重新下载算 hash（无短路）。
        """
        entry: PackageEntry | None = self.registry.get(name)
        if entry is None:
            raise PackageNotFoundError(name)
        pkg: Package | None = await Package.get_or_none(name=name)
        if pkg is None:
            raise PackageNotFoundError(name)

        snapshot: _VersionSnapshot | None = await self.collect_version(pkg, entry)
        if snapshot is None:
            self._last_collected[name] = _utcnow()
            raise RuntimeError(f"采集 {name} 版本失败")

        await self.collect_hashes(entry, snapshot)
        self._last_collected[name] = _utcnow()

        read: tuple[PackageInfo, datetime] | None = await self._read_info(
            name, _DEFAULT_ALGORITHM, entry
        )
        if read is not None:
            return read[0]
        # 刚落 success version 却读不到属异常兜底，用快照内容占位
        return PackageInfo(
            name=name, version=snapshot.version, urls=snapshot.urls, hashes={}
        )

    async def collect_version(
        self, pkg: Package, entry: PackageEntry
    ) -> _VersionSnapshot | None:
        """版本域：按解析器类型分派。

        - 安装包解析器（``PackageFileVersionParser``，如 deb/QQ）：定位安装包
          URL → 流式下载头部 → 从文件内容（deb control 段）提取版本；
        - 其余：fetch_text 版本源响应 → parse_version。

        失败（抓取/解析）落 failed 审计行并返回 None；成功落 success 行并返回快照。
        """
        parser: BaseParser = entry.parser
        if isinstance(parser, PackageFileVersionParser):
            return await self._collect_version_from_package(pkg, entry, parser)

        response_data: str | None = await self.fetcher.fetch_text(
            entry.fetch_url, parser.get_request_headers()
        )
        if response_data is None:
            await self.persist_version_failure(
                pkg, f"无法获取版本源: {entry.fetch_url}"
            )
            return None

        version: str | None = parser.parse_version(response_data)
        if not version:
            await self.persist_version_failure(pkg, "无法解析版本号")
            return None

        urls: dict[str, str] = {}
        for arch in entry.archs:
            url: str | None = parser.parse_url(arch, response_data)
            if url:
                urls[arch.value] = url
            else:
                logger.warning("无法获取 %s 的 %s 架构下载 URL", pkg.name, arch.value)

        version_row: PackageVersion = await self.persist_version(pkg, version, urls)
        logger.info("采集 %s 版本完成：version=%s", pkg.name, version)
        return _VersionSnapshot(version_row, version, urls)

    async def _collect_version_from_package(
        self,
        pkg: Package,
        entry: PackageEntry,
        parser: PackageFileVersionParser,
    ) -> _VersionSnapshot | None:
        """安装包路径版本域：定位安装包 URL → 下载头部 → 提取版本 → 落库。

        各架构提取到的版本必须一致才落库（防上游部分发布——否则 hash 会挂到
        与 URL 不符的版本号下，与 TraeParser 的一致性契约相同）；个别架构
        定位/下载/提取失败仅告警跳过，不连坐其他架构。
        """
        urls: dict[str, str]
        error: str | None
        urls, error = await self._resolve_package_urls(pkg, entry, parser)
        if error is not None:
            await self.persist_version_failure(pkg, error)
            return None

        versions: set[str] = set()
        if urls:
            # 逐架构并发提取（与 hash 域 gather 并发风格一致；QQ 多架构串行
            # 签名+下载会成倍放大采集延迟）
            extracted: list[str | None] = await asyncio.gather(
                *[
                    self._version_from_package(pkg.name, arch_value, raw, parser)
                    for arch_value, raw in urls.items()
                ]
            )
            versions = {v for v in extracted if v is not None}

        if not versions:
            await self.persist_version_failure(pkg, "无法从安装包文件提取版本号")
            return None
        if len(versions) > 1:
            await self.persist_version_failure(
                pkg, f"各架构安装包版本不一致: {sorted(versions)}"
            )
            return None

        version = versions.pop()
        version_row: PackageVersion = await self.persist_version(pkg, version, urls)
        logger.info("采集 %s 版本完成（安装包提取）：version=%s", pkg.name, version)
        return _VersionSnapshot(version_row, version, urls)

    async def _resolve_package_urls(
        self,
        pkg: Package,
        entry: PackageEntry,
        parser: PackageFileVersionParser,
    ) -> tuple[dict[str, str], str | None]:
        """定位各架构安装包 URL：静态配置优先，否则经版本源响应 parse_url。

        返回 ``(urls, error)``：error 非 None 表示整体失败（无法获取版本源或
        一个架构都未定位到），须走版本失败落库；仅缺个别架构则告警跳过。
        urls 以 entry.archs 为键集，与文本路径口径一致。
        """
        static_urls: dict[str, str] | None = parser.package_download_urls()
        if static_urls is not None:
            urls: dict[str, str] = {}
            for arch in entry.archs:
                url: str | None = static_urls.get(arch.value)
                if url:
                    urls[arch.value] = url
                else:
                    logger.warning(
                        "无法获取 %s 的 %s 架构下载 URL", pkg.name, arch.value
                    )
            error: str | None = (
                None if urls else "静态配置未提供任何已配置架构的安装包 URL"
            )
            return urls, error

        response_data: str | None = await self.fetcher.fetch_text(
            entry.fetch_url, parser.get_request_headers()
        )
        if response_data is None:
            return {}, f"无法获取版本源: {entry.fetch_url}"

        urls = {}
        for arch in entry.archs:
            url = parser.parse_url(arch, response_data)
            if url:
                urls[arch.value] = url
            else:
                logger.warning("无法获取 %s 的 %s 架构下载 URL", pkg.name, arch.value)
        error = None if urls else "无法从版本源解析任何架构的安装包 URL"
        return urls, error

    async def _version_from_package(
        self,
        pkg_name: str,
        arch_value: str,
        raw_url: str,
        parser: PackageFileVersionParser,
    ) -> str | None:
        """单架构安装包版本提取：resolve_raw_url（鉴权钩子）→ 下载头部 → 解析。

        任一环节失败仅告警返回 None，不抛出（与 hash 域逐架构独立失败同风格）。
        """
        try:
            resolved: str | None = await parser.resolve_raw_url(arch_value, raw_url)
        except Exception:
            logger.exception("%s 的 %s 架构 resolve_raw_url 异常", pkg_name, arch_value)
            return None
        if resolved is None:
            logger.warning(
                "%s 的 %s 架构无法获取可下载 URL，跳过版本提取", pkg_name, arch_value
            )
            return None

        head: bytes | None = await self.fetcher.fetch_head(
            resolved, parser.PACKAGE_HEAD_MAX_BYTES
        )
        if head is None:
            logger.warning(
                "%s 的 %s 架构安装包头部下载失败，跳过版本提取", pkg_name, arch_value
            )
            return None

        try:
            version: str | None = parser.version_from_package_head(head)
        except Exception:
            # 「任一环节失败不抛出」契约的兜底：parser 实现若漏捕获解析异常，
            # 在此拦下转逐架构跳过，不让整个采集逃逸失败
            logger.exception("%s 的 %s 架构安装包版本解析异常", pkg_name, arch_value)
            return None
        if version is None:
            logger.warning("%s 的 %s 架构安装包版本提取失败", pkg_name, arch_value)
        return version

    async def collect_hashes(
        self,
        entry: PackageEntry,
        snapshot: _VersionSnapshot,
    ) -> list[_HashResult]:
        """hash 域：逐 arch resolve_raw_url（QQ 签名）→ 并发下载一次算全部算法 → 逐行落库。

        每个架构单次下载同时产出全部 ``_ALL_ALGORITHMS`` 的 digest（单流多 hash），
        使任意 algorithm 的查询都能命中。失败的架构对每种算法都落 ``status=failed`` 行；
        version 已先行落库，hash 失败不影响它。
        """
        parser: BaseParser = entry.parser

        async def _resolve_one(arch: ArchEnum) -> tuple[str, str | None]:
            arch_value: str = arch.value
            raw: str | None = snapshot.urls.get(arch_value)
            if not raw:
                return arch_value, None
            try:
                resolved: str | None = await parser.resolve_raw_url(arch, raw)
            except Exception:
                logger.exception(
                    "%s 的 %s 架构 resolve_raw_url 异常", entry.name, arch_value
                )
                return arch_value, None
            if resolved is None:
                logger.warning(
                    "%s 的 %s 架构无法获取可下载 URL，跳过 hash",
                    entry.name,
                    arch_value,
                )
            return arch_value, resolved

        resolved_results: list[tuple[str, str | None]] = await asyncio.gather(
            *[_resolve_one(arch) for arch in entry.archs]
        )

        download_urls: dict[str, str] = {
            av: r for av, r in resolved_results if r is not None
        }
        downloaded: dict[str, dict[str, str] | None] = (
            await self.fetcher.fetch_and_hash_many(download_urls, _ALL_ALGORITHMS)
            if download_urls
            else {}
        )

        results: list[_HashResult] = []
        for arch_value, resolved in resolved_results:
            raw: str | None = snapshot.urls.get(arch_value)
            if resolved is None:
                # 无可下载 URL：每种算法都记失败行
                for algo in _ALL_ALGORITHMS:
                    results.append(
                        _HashResult(arch_value, algo, None, raw, _ERR_NO_DOWNLOAD_URL)
                    )
                continue
            digests: dict[str, str] | None = downloaded.get(arch_value)
            for algo in _ALL_ALGORITHMS:
                digest: str | None = digests.get(algo) if digests else None
                results.append(
                    _HashResult(
                        arch_value,
                        algo,
                        digest,
                        raw,
                        None if digest is not None else _ERR_HASH_FAILED,
                    )
                )
        await self.persist_hashes(snapshot.version_row, results)
        ok_archs = sum(1 for av, r in resolved_results if r is not None)
        logger.info(
            "采集 %s hash 完成：%d/%d 架构成功（每架构 %d 种算法）",
            entry.name,
            ok_archs,
            len(resolved_results),
            len(_ALL_ALGORITHMS),
        )
        return results

    # ── 落库（各自独立事务） ────────────────────────────────────────────

    async def persist_version(
        self, pkg: Package, version: str, urls: dict[str, str]
    ) -> PackageVersion:
        """落一条成功版本快照（含 urls JSON），独立事务，立即对查询可见"""
        async with in_transaction():
            return await PackageVersion.create(
                package=pkg,
                version=version,
                urls=json.dumps(urls, ensure_ascii=False),
                status="success",
                error=None,
            )

    async def persist_version_failure(self, pkg: Package, error: str) -> None:
        """记录版本抓取失败审计行。落库异常被吞只记日志，避免逃逸到调度器"""
        try:
            await PackageVersion.create(
                package=pkg, version=None, urls=None, status="failed", error=error
            )
        except Exception:
            logger.exception("记录版本失败落库异常：%s", pkg.name)
            return
        logger.warning("采集 %s 版本失败已记录：%s", pkg.name, error)

    async def persist_hashes(
        self,
        version_row: PackageVersion,
        results: Iterable[_HashResult],
    ) -> None:
        """逐「架构 × 算法」落 hash 行（成功/失败均落），独立事务。

        失败行 hash_value=NULL、status=failed、记录 error，便于审计与重试观察。
        """
        rows: list[PackageHash] = [
            PackageHash(
                version=version_row,
                arch=r.arch_value,
                algorithm=r.algorithm,
                hash_value=r.hash_value,
                url=r.url,
                status="success" if r.hash_value is not None else "failed",
                error=r.error,
            )
            for r in results
        ]
        async with in_transaction():
            await PackageHash.bulk_create(rows)
