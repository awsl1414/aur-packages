"""包版本采集编排服务。

只负责版本与下载 URL：抓取版本源（或安装包头部）→ 解析版本号与各架构 URL →
落库 ``package_versions``。校验和由消费方（aur-auto-update）下载后本地计算，
本服务不下载安装包体、不计算 hash。

查询接口 ``get_info`` 纯读 DB，不触发任何采集；采集只由定时调度与显式 refresh
驱动。``download_urls`` 为查询时经 ``resolve_raw_url`` 实时生成（仅签名/鉴权
RPC，如 QQ GetSign），失败降级不影响响应。
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from tortoise.transactions import in_transaction

from aur_metadata.fetcher import Fetcher
from aur_metadata.models import Package, PackageVersion
from aur_metadata.parsers.base import BaseParser, PackageFileVersionParser
from aur_metadata.registry import PackageEntry, PackageRegistry
from aur_metadata.schemas import PackageInfo

logger = logging.getLogger(__name__)


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


def _utcnow() -> datetime:
    return datetime.now(UTC)


class PackageService:
    """编排版本抓取、落库与查询。

    独占采集与查询、per-package 锁与节流；调度器与手动刷新均委托本服务。
    """

    def __init__(
        self,
        fetcher: Fetcher,
        registry: PackageRegistry,
        min_collect_interval_seconds: int = 0,
    ) -> None:
        self.fetcher = fetcher
        self.registry = registry
        self._min_collect_interval = min_collect_interval_seconds
        # per-package 采集锁：保证同包不重入（QQ 签名 / 安装包头部下载较慢）
        self._locks: dict[str, asyncio.Lock] = {}
        # per-package 上次采集完成时间（仅内存，重启重置；节流共用）
        self._last_collected: dict[str, datetime] = {}

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
        正被持有的锁不剔除——剔除后新 collect 会另建新锁，出现同包新旧两把锁并发采集；
        遗留锁在采集结束后的下次 reload 自然回收。
        """
        self._last_collected = {
            n: t for n, t in self._last_collected.items() if n in keep
        }
        self._locks = {
            n: lk for n, lk in self._locks.items() if n in keep or lk.locked()
        }

    def _get_lock(self, name: str) -> asyncio.Lock:
        """取 per-package 采集锁，不存在则创建并登记"""
        lock = self._locks.get(name)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[name] = lock
        return lock

    # ── 查询（纯读） ────────────────────────────────────────────────────

    async def list_packages(self) -> list[str]:
        """返回所有启用（enabled）的包名"""
        return [entry.name for entry in self.registry.list_all()]

    async def get_info(self, name: str) -> PackageInfo:
        """纯 DB 读最新成功版本快照，并实时生成 download_urls。

        不触发采集、不下载安装包体；download_urls 经 ``resolve_raw_url`` 实时
        签名（QQ 等鉴权源为临时链接，会过期），单架构失败置 None 不影响响应。
        包已注册但从未采集成功则抛 ``DataNotReadyError``（路由层转「数据未就绪」）。
        """
        entry: PackageEntry | None = self.registry.get(name)
        if entry is None:
            raise PackageNotFoundError(name)

        info: PackageInfo | None = await self._read_info(name, entry)
        if info is None:
            raise DataNotReadyError(name)
        return await self._attach_download_urls(entry, info)

    async def _read_info(
        self, name: str, entry: PackageEntry
    ) -> PackageInfo | None:
        """从 DB 读最新成功 version 行；无则返回 None。

        urls 以**当前** entry.archs 为键集：reload 改动 archs 后，落库时捕获的
        旧 urls 不再原样泄露（被删架构不出现，新架构无 URL 则缺）。
        """
        pkg: Package | None = await Package.get_or_none(name=name)
        if pkg is None:
            return None

        latest: PackageVersion | None = (
            await PackageVersion.filter(package=pkg, status="success")
            .order_by("-fetched_at", "-id")
            .first()
        )
        if latest is None or not latest.version:
            return None

        persisted_urls: dict[str, str] = json.loads(latest.urls) if latest.urls else {}
        urls: dict[str, str] = {
            arch.value: persisted_urls[arch.value]
            for arch in entry.archs
            if arch.value in persisted_urls
        }
        return PackageInfo(name=name, version=latest.version, urls=urls)

    async def _attach_download_urls(
        self, entry: PackageEntry, info: PackageInfo
    ) -> PackageInfo:
        """逐架构经 ``resolve_raw_url`` 生成实时可下载链接（download_urls）。

        仅签名/鉴权类 RPC（如 QQ GetSign），不下载安装包体；默认恒等实现
        的解析器无网络开销，结果与 ``urls`` 相同。单架构失败置 ``None``
        仅记日志——download_urls 是附加能力，绝不拖垮查询响应。键集与
        ``urls`` 对齐，消费方可按下标一一配对。
        """
        parser: BaseParser = entry.parser

        async def _resolve(arch_value: str, raw_url: str) -> tuple[str, str | None]:
            try:
                resolved: str | None = await parser.resolve_raw_url(arch_value, raw_url)
            except Exception:
                logger.exception(
                    "%s 的 %s 架构 resolve_raw_url 异常", entry.name, arch_value
                )
                resolved = None
            return arch_value, resolved

        pairs: list[tuple[str, str | None]] = await asyncio.gather(
            *[_resolve(arch_value, raw) for arch_value, raw in info.urls.items()]
        )
        return info.model_copy(update={"download_urls": dict(pairs)})

    # ── 采集（写） ──────────────────────────────────────────────────────

    async def collect_version(self, name: str) -> PackageInfo:
        """采集一次版本与 URL 并落库，返回最新快照（供定时任务调用，不拒绝节流）"""
        async with self._get_lock(name):
            return await self._collect_version_locked(name)

    async def collect_version_now(self, name: str) -> PackageInfo:
        """手动触发采集：节流检查与采集同处 per-package 锁内（消除 check-then-act）。

        节流内抛 ``CollectThrottledError`` → 路由层转 429。
        """
        if self.registry.get(name) is None:
            raise PackageNotFoundError(name)
        async with self._get_lock(name):
            if self.is_throttled(name):
                raise CollectThrottledError(name)
            return await self._collect_version_locked(name)

    async def _collect_version_locked(self, name: str) -> PackageInfo:
        """实际采集逻辑（调用方已持 per-package 锁）。

        版本域失败（已落 failed 审计行）抛 RuntimeError：refresh 路径据此转 502，
        定时路径自行吞掉。成功后回读 DB 返回最新快照。
        """
        entry: PackageEntry | None = self.registry.get(name)
        if entry is None:
            raise PackageNotFoundError(name)
        pkg: Package | None = await Package.get_or_none(name=name)
        if pkg is None:
            raise PackageNotFoundError(name)

        snapshot: _VersionSnapshot | None = await self._collect_from_source(pkg, entry)
        self._last_collected[name] = _utcnow()
        if snapshot is None:
            raise RuntimeError(f"采集 {name} 版本失败")

        info: PackageInfo | None = await self._read_info(name, entry)
        if info is not None:
            return info
        # 刚落 success version 却读不到属异常兜底，用快照内容占位
        return PackageInfo(name=name, version=snapshot.version, urls=snapshot.urls)

    @staticmethod
    def _urls_from_response(
        pkg_name: str, entry: PackageEntry, parser: BaseParser, response_data: str
    ) -> dict[str, str]:
        """从版本源响应逐架构提取安装包 URL；缺失架构记普通警告并跳过。"""
        urls: dict[str, str] = {}
        for arch in entry.archs:
            url: str | None = parser.parse_url(arch, response_data)
            if url:
                urls[arch.value] = url
            else:
                logger.warning("无法获取 %s 的 %s 架构下载 URL", pkg_name, arch.value)
        return urls

    async def _collect_from_source(
        self, pkg: Package, entry: PackageEntry
    ) -> _VersionSnapshot | None:
        """按解析器类型分派版本采集。

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

        urls = self._urls_from_response(pkg.name, entry, parser, response_data)

        version_row: PackageVersion = await self.persist_version(pkg, version, urls)
        logger.info("采集 %s 版本完成：version=%s", pkg.name, version)
        return _VersionSnapshot(version_row, version, urls)

    async def _collect_version_from_package(
        self,
        pkg: Package,
        entry: PackageEntry,
        parser: PackageFileVersionParser,
    ) -> _VersionSnapshot | None:
        """安装包路径版本采集：定位安装包 URL → 下载头部 → 提取版本 → 落库。

        各架构提取到的版本必须一致才落库（防上游部分发布——否则 URL 会与
        版本号不符，与 TraeParser 的一致性契约相同）；个别架构定位/下载/提取
        失败仅告警跳过，不连坐其他架构。
        """
        urls: dict[str, str]
        error: str | None
        urls, error = await self._resolve_package_urls(pkg, entry, parser)
        if error is not None:
            await self.persist_version_failure(pkg, error)
            return None

        versions: set[str] = set()
        if urls:
            # 逐架构并发提取：QQ 多架构串行签名 + 下载会成倍放大采集延迟
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

        urls = self._urls_from_response(pkg.name, entry, parser, response_data)
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

        任一环节失败仅告警返回 None，不抛出（逐架构独立失败）。
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
            # deb 头部解压是 CPU 密集操作（control.tar 封顶 32MB），放入线程池
            # 避免阻塞事件循环
            version: str | None = await asyncio.to_thread(
                parser.version_from_package_head, head
            )
        except Exception:
            # 「任一环节失败不抛出」契约的兜底：parser 实现若漏捕获解析异常，
            # 在此拦下转逐架构跳过，不让整个采集逃逸失败
            logger.exception("%s 的 %s 架构安装包版本解析异常", pkg_name, arch_value)
            return None
        if version is None:
            logger.warning("%s 的 %s 架构安装包版本提取失败", pkg_name, arch_value)
        return version

    # ── 落库 ────────────────────────────────────────────────────────────

    async def persist_version(
        self, pkg: Package, version: str, urls: dict[str, str]
    ) -> PackageVersion:
        """落一条成功版本快照（含 urls JSON），独立事务，立即对查询可见。

        版本未变时复用当前最新 success 行，只刷新 ``urls`` 与 ``fetched_at``——
        否则每次采集都插新行，历史表会随采集轮次无限膨胀，且下游读到的最新行
        与上一轮内容等价。版本变化或首次采集才插新行。
        """
        urls_json: str = json.dumps(urls, ensure_ascii=False)
        latest: PackageVersion | None = (
            await PackageVersion.filter(package=pkg, status="success")
            .order_by("-fetched_at", "-id")
            .first()
        )
        if latest is not None and latest.version == version:
            # auto_now_add 不会在 save 时刷新，须显式 update
            await PackageVersion.filter(id=latest.id).update(
                urls=urls_json, fetched_at=_utcnow()
            )
            await latest.refresh_from_db()
            return latest

        async with in_transaction():
            return await PackageVersion.create(
                package=pkg,
                version=version,
                urls=urls_json,
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
