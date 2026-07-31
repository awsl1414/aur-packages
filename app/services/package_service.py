"""包查询编排服务"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from tortoise.transactions import in_transaction

from app.constants import ArchEnum, HashAlgorithmEnum
from app.fetcher import Fetcher
from app.models import Package, PackageHash, PackageVersion
from app.parsers.base import BaseParser
from app.registry import PackageEntry, PackageRegistry
from app.schemas import PackageInfo

logger = logging.getLogger(__name__)

_STATUS_SUCCESS = "success"
_STATUS_PARTIAL = "partial"
_STATUS_FAILED = "failed"


class PackageNotFoundError(KeyError):
    """请求的包未在注册表中"""


class CollectThrottledError(Exception):
    """包采集触发节流（两次采集间隔小于 min_collect_interval_seconds）"""


class PackageService:
    """编排 fetch + parse + hash 计算的查询服务"""

    def __init__(
        self,
        fetcher: Fetcher,
        registry: PackageRegistry,
        min_collect_interval_seconds: int = 0,
    ) -> None:
        self.fetcher = fetcher
        self.registry = registry
        self._min_collect_interval = min_collect_interval_seconds
        # per-package 上次采集完成时间（仅内存，重启重置；TTL/定时兜底）
        self._last_collected: dict[str, datetime] = {}

    def is_throttled(self, name: str) -> bool:
        """该包是否处于采集节流窗口内（距上次采集不足最小间隔）"""
        last: datetime | None = self._last_collected.get(name)
        if last is None or self._min_collect_interval <= 0:
            return False
        elapsed = datetime.now(UTC) - last
        return elapsed < timedelta(seconds=self._min_collect_interval)

    def prune_last_collected(self, keep: set[str]) -> None:
        """剔除不在 ``keep`` 集合中的包的节流记录。

        reload 后已删除/停用的包不再采集，其节流记录应清理，避免长生命周期下
        ``_last_collected`` 只增不减。
        """
        self._last_collected = {
            n: t for n, t in self._last_collected.items() if n in keep
        }

    async def list_packages(self) -> list[str]:
        """返回所有启用（enabled）的包名"""
        return [entry.name for entry in self.registry.list_all()]

    async def get_info(
        self,
        name: str,
        hash_algorithm: str = HashAlgorithmEnum.B2.value,
    ) -> PackageInfo:
        """实时查询指定包的版本号、各架构下载 URL 与文件 hash。

        步骤：
        1. 查注册表获取 entry（不存在抛 PackageNotFoundError → 路由层转 404）
        2. 拉取 fetch_url（带 parser 专属请求头）
        3. parse_version → version（失败抛 RuntimeError → 路由层转 502）
        4. 遍历 entry.archs 调 parse_url → urls 字典
        5. 并发调 resolve_url（QQ 走签名）获取各架构可下载 URL
           → fetch_and_hash_many 并发流式下载计算 hash；失败的 arch 记 None + warning
        """
        entry: PackageEntry | None = self.registry.get(name)
        if entry is None:
            raise PackageNotFoundError(name)

        parser: BaseParser = entry.parser

        response_data: str | None = await self.fetcher.fetch_text(
            entry.fetch_url, parser.get_request_headers()
        )
        if response_data is None:
            raise RuntimeError(f"无法获取 {name} 的版本信息")

        version: str | None = parser.parse_version(response_data)
        if version is None:
            raise RuntimeError(f"无法解析 {name} 的版本号")

        urls: dict[str, str] = {}
        for arch in entry.archs:
            url: str | None = parser.parse_url(arch, response_data)
            if url:
                urls[arch.value] = url
            else:
                logger.warning("无法获取 %s 的 %s 架构下载 URL", name, arch.value)

        hashes: dict[str, str | None] = await self._compute_hashes(
            entry, parser, response_data, hash_algorithm
        )

        # 记录采集完成时间，供 refresh / GET 回源节流判断
        self._last_collected[name] = datetime.now(UTC)
        return PackageInfo(name=name, version=version, urls=urls, hashes=hashes)

    async def get_info_cached(
        self,
        name: str,
        hash_algorithm: str,
        max_age_seconds: int,
    ) -> PackageInfo:
        """查询入口：优先 DB 新鲜快照；过期/缺失则回源，节流内拒绝回源以防空放大下载。

        - 命中新鲜快照 → 返回
        - 未命中且未节流 → 回源 get_info（实时下载）并落库，使后续节流窗口内的
          请求能命中新鲜快照或 stale 降级，而非被节流拒绝
        - 未命中且节流内 → 降级返回 DB 该算法 stale 快照（忽略 TTL）；
          若该算法无任何 stale（如变换 algorithm 绕过），抛 CollectThrottledError → 429
        """
        cached: PackageInfo | None = await self._try_cache(
            name, hash_algorithm, max_age_seconds
        )
        if cached is not None:
            logger.info("命中 DB 缓存：%s", name)
            return cached

        if self.is_throttled(name):
            stale: PackageInfo | None = await self._try_cache(
                name, hash_algorithm, None
            )
            if stale is not None:
                logger.info("节流内回源降级返回 stale：%s", name)
                return stale
            # 节流内且无可用 stale（含变换 algorithm 绕过）→ 拒绝回源
            raise CollectThrottledError(name)

        info: PackageInfo = await self.get_info(name, hash_algorithm=hash_algorithm)
        # 回源也落库：get_info 已写 _last_collected 开启节流窗口，若不落库则窗口内
        # 后续请求既无新鲜快照也无 stale → 429。落库后整链路自洽（与定时/refresh 一致）
        await self._persist_fetch(name, info, hash_algorithm)
        return info

    async def _persist_fetch(
        self, name: str, info: PackageInfo, algorithm: str
    ) -> None:
        """回源落库：按 name 取 Package 后复用 persist_result。Package 不存在则跳过。

        registry 由 DB 构建，能进入回源说明包必在 DB，此处仍兜底防异常。
        """
        pkg: Package | None = await Package.get_or_none(name=name)
        if pkg is None:
            logger.warning("回源落库时 %s 在 DB 不存在，跳过", name)
            return
        await self.persist_result(pkg, info, algorithm=algorithm)

    async def persist_result(
        self, pkg: Package, info: PackageInfo, algorithm: str
    ) -> None:
        """按版本号与各架构 hash 命中情况判定 success/partial/failed 并落库。

        expected 架构集合取自 ``info.hashes`` 的 key（即本次实际采集的架构，源自
        registry entry.archs），而非 DB 的 ``pkg.archs``——后者可能与内存 registry
        不同步（运维改 DB 未 reload），导致 status 误判。version 与 hashes 在单事务内
        写入，避免中途失败留下不完整快照被后续 _try_cache 当作完整结果返回。
        """
        hashes: dict[str, str | None] = info.hashes or {}
        if not info.version:
            await self.persist_failure(pkg, "未解析到版本号")
            return
        if hashes and all(v is None for v in hashes.values()):
            await self.persist_failure(pkg, "全部架构 hash 计算失败")
            return

        # 缺失架构不会出现（hashes 覆盖 entry 全部 archs），仅需看 hash 为 None 的架构
        bad: set[str] = {a for a, v in hashes.items() if v is None}
        status: str = _STATUS_PARTIAL if bad else _STATUS_SUCCESS

        async with in_transaction():
            version: PackageVersion = await PackageVersion.create(
                package=pkg, version=info.version, status=status, error=None
            )
            if hashes:
                await PackageHash.bulk_create(
                    [
                        PackageHash(
                            version=version,
                            arch=arch_value,
                            algorithm=algorithm,
                            hash_value=h,
                            url=info.urls.get(arch_value),
                        )
                        for arch_value, h in hashes.items()
                    ]
                )
        logger.info(
            "采集 %s 完成：version=%s status=%s", pkg.name, info.version, status
        )

    async def persist_failure(self, pkg: Package, error: str) -> None:
        """记录失败快照便于审计。

        落库异常被吞掉只记日志——调用方（_collect）以此方法兜底，若它再上抛会让
        整个采集异常逃逸到 APScheduler，与「单包失败不影响调度」的契约冲突。
        """
        try:
            await PackageVersion.create(
                package=pkg, version=None, status=_STATUS_FAILED, error=error
            )
        except Exception:
            logger.exception("记录采集失败落库异常：%s", pkg.name)
            return
        logger.warning("采集 %s 失败已记录：%s", pkg.name, error)

    async def _try_cache(
        self,
        name: str,
        hash_algorithm: str,
        max_age_seconds: int | None,
    ) -> PackageInfo | None:
        """尝试从 DB 取快照；未命中返回 None。

        命中条件：最新 success/partial 快照有 version、含所请求算法的 hash 记录。
        ``max_age_seconds`` 非 None 时还要求快照在该年龄内（新鲜）；为 None 则忽略年龄
        （用于节流降级时返回 stale）。
        """
        pkg: Package | None = await Package.get_or_none(name=name)
        if pkg is None:
            return None

        latest: PackageVersion | None = (
            await PackageVersion.filter(package=pkg, status__in=["success", "partial"])
            .order_by("-fetched_at", "-id")
            .first()
        )
        if latest is None or not latest.version or latest.fetched_at is None:
            return None

        if max_age_seconds is not None:
            fetched_at: datetime = latest.fetched_at
            # Tortoise 默认返回 aware UTC，兜底处理 naive 情况
            if fetched_at.tzinfo is None:
                fetched_at = fetched_at.replace(tzinfo=UTC)
            cutoff: datetime = datetime.now(UTC) - timedelta(seconds=max_age_seconds)
            if fetched_at < cutoff:
                return None  # 过期

        records: list[PackageHash] = await PackageHash.filter(
            version=latest, algorithm=hash_algorithm
        )
        if not records:
            return None  # 该算法无记录 → 回源
        hashes: dict[str, str | None] = {h.arch: h.hash_value for h in records}
        urls: dict[str, str] = {h.arch: h.url for h in records if h.url}
        return PackageInfo(name=name, version=latest.version, urls=urls, hashes=hashes)

    async def _compute_hashes(
        self,
        entry: PackageEntry,
        parser: BaseParser,
        response_data: str,
        hash_algorithm: str,
    ) -> dict[str, str | None]:
        """并发解析所有架构的下载 URL（签名）并流式下载计算 hash。

        两阶段并发：
        1. 并发调用 resolve_url 获取各架构的可下载 URL
        2. 并发下载并计算 hash（通过 fetch_and_hash_many，Semaphore 限流）

        resolve_url 失败或下载失败的架构记为 None，不中断整体流程。
        """

        async def _resolve_one(arch: ArchEnum) -> tuple[str, str | None]:
            arch_value: str = arch.value
            try:
                resolved: str | None = await parser.resolve_url(arch, response_data)
            except Exception:
                logger.exception(
                    "%s 的 %s 架构 resolve_url 异常", entry.name, arch_value
                )
                resolved = None
            if resolved is None:
                logger.warning(
                    "%s 的 %s 架构无法获取可下载 URL，跳过 hash",
                    entry.name,
                    arch_value,
                )
            return arch_value, resolved

        # 阶段 1：并发解析各架构的可下载 URL
        resolved_results: list[tuple[str, str | None]] = await asyncio.gather(
            *[_resolve_one(arch) for arch in entry.archs]
        )

        # 阶段 2：过滤后并发下载并计算 hash
        hashes: dict[str, str | None] = {}
        urls: dict[str, str] = {}
        for arch_value, resolved in resolved_results:
            if resolved is not None:
                urls[arch_value] = resolved
            else:
                hashes[arch_value] = None

        if urls:
            downloaded: dict[str, str | None] = await self.fetcher.fetch_and_hash_many(
                urls, hash_algorithm
            )
            hashes.update(downloaded)

        return hashes
