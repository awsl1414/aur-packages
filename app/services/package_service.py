"""包查询编排服务"""

import asyncio
import logging

from app.constants import ArchEnum, HashAlgorithmEnum
from app.fetcher import Fetcher
from app.parsers.base import BaseParser
from app.registry import PackageEntry, PackageRegistry
from app.schemas import PackageInfo

logger = logging.getLogger(__name__)


class PackageNotFoundError(KeyError):
    """请求的包未在注册表中"""


class PackageService:
    """编排 fetch + parse + 可选 hash 计算的查询服务"""

    def __init__(self, fetcher: Fetcher, registry: PackageRegistry) -> None:
        self.fetcher = fetcher
        self.registry = registry

    async def list_packages(self) -> list[str]:
        """返回所有已注册包名"""
        return [entry.name for entry in self.registry.list_all()]

    async def get_info(
        self,
        name: str,
        with_hash: bool = False,
        hash_algorithm: str = HashAlgorithmEnum.B2.value,
    ) -> PackageInfo:
        """查询指定包的最新版本与可选信息。

        步骤：
        1. 查注册表获取 entry（不存在抛 PackageNotFoundError → 路由层转 404）
        2. 拉取 fetch_url（带 parser 专属请求头）
        3. parse_version → version（失败抛 RuntimeError → 路由层转 502）
        4. 遍历 entry.archs 调 parse_url → urls 字典
        5. with_hash=True 时：并发调 resolve_url（QQ 走签名）获取各架构 URL
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

        hashes: dict[str, str | None] | None = None
        if with_hash:
            hashes = await self._compute_hashes(
                entry, parser, response_data, hash_algorithm
            )

        return PackageInfo(name=name, version=version, urls=urls, hashes=hashes)

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

        # Phase 1: 并发解析所有架构的下载 URL
        resolved_results: list[tuple[str, str | None]] = await asyncio.gather(
            *[_resolve_one(arch) for arch in entry.archs]
        )

        # Phase 2: 过滤 + 并发下载
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
