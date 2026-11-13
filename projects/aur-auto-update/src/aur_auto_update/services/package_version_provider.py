"""包版本来源：优先 metadata API，失败时为 GitHub 来源包回退到本地 release 解析。

回退只在 metadata 请求失败时发生（网络错误、非 200、解析失败）；metadata 在线
时一律采用其响应，不做版本新旧比较——陈旧快照由 metadata 的定时采集负责。
"""

import logging

from aur_auto_update.config import PackageConfig
from aur_auto_update.fetcher import Fetcher
from aur_auto_update.parsers.api_parser import ApiParser, ParsedPackage
from aur_auto_update.services.github_release_service import GithubReleaseService

logger = logging.getLogger(__name__)


class PackageVersionProvider:
    """按「metadata 优先、GitHub 回退」获取包的版本与下载 URL。"""

    def __init__(
        self,
        fetcher: Fetcher,
        parser: ApiParser,
        github: GithubReleaseService,
    ) -> None:
        self._fetcher = fetcher
        self._parser = parser
        self._github = github

    async def fetch(
        self, package_config: PackageConfig, metadata_url: str
    ) -> ParsedPackage | None:
        """获取版本信息；metadata 失败且包配置了 ``github`` 时才回退。"""
        parsed: ParsedPackage | None = await self._from_metadata(
            package_config.name, metadata_url
        )
        if parsed is not None:
            return parsed

        if package_config.github is None:
            logger.error("  无法从 metadata 获取 %s 的版本信息", package_config.name)
            return None

        logger.warning(
            "  metadata 不可用，%s 回退到 GitHub release 解析", package_config.name
        )
        parsed = await self._github.fetch(package_config)
        if parsed is None:
            logger.error("  GitHub 回退也未能获取 %s 的版本信息", package_config.name)
        return parsed

    async def _from_metadata(
        self, package_name: str, metadata_url: str
    ) -> ParsedPackage | None:
        """请求 metadata 并解析；任一环节失败返回 None（由调用方决定是否回退）。"""
        response_data: str | None = await self._fetcher.fetch_text(metadata_url)
        if not response_data:
            return None
        return self._parser.parse(response_data)
