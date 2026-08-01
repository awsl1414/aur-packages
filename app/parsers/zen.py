"""Zen Browser 每夜版解析器

从 GitHub Releases API 的固定标签 ``twilight-1``（发布内容每天更新）提取版本号与
各架构 asset 链接。release ``name`` 形如 ``"Twilight build - 1.20t (...)"``，
从中正则取版本号（如 ``1.20t``）。
"""

import logging
import re
from typing import Any

from app.constants import ArchEnum

from .base import BaseParser

logger = logging.getLogger(__name__)

# 架构到 GitHub Release asset 名称的映射
_ARCH_ASSET_MAP: dict[str, str] = {
    ArchEnum.X86_64.value: "zen.linux-x86_64.tar.xz",
    ArchEnum.AARCH64.value: "zen.linux-aarch64.tar.xz",
}


class ZenParser(BaseParser):
    """Zen Browser 每夜版解析器：GitHub Releases JSON 提取版本与 asset 链接"""

    # release name 内版本号片段，如 "1.20t" / "1.5a"
    _VERSION_PATTERN: re.Pattern[str] = re.compile(r"(\d+\.\d+[a-z]?)")

    def parse_version(self, response_data: str | Any) -> str | None:
        """从 release ``name`` 正则提取版本号"""
        if not isinstance(response_data, str):
            return None
        data: dict[str, Any] | None = self._parse_json_dict(response_data)
        if data is None:
            return None
        release_name: str | None = data.get("name")
        if not release_name:
            logger.warning("Zen: Release 缺少 name 字段")
            return None
        match: re.Match[str] | None = self._VERSION_PATTERN.search(release_name)
        if not match:
            logger.warning("Zen: 无法从 release name 提取版本号: %s", release_name)
            return None
        return match.group(1)

    def parse_url(self, arch: ArchEnum | str, response_data: str | Any) -> str | None:
        """从 ``assets[]`` 中按名称匹配指定架构的 ``browser_download_url``"""
        if not isinstance(response_data, str):
            return None
        data: dict[str, Any] | None = self._parse_json_dict(response_data)
        if data is None:
            return None

        arch_value = self._arch_value(arch)
        target: str | None = _ARCH_ASSET_MAP.get(arch_value)
        if target is None:
            logger.warning("Zen: 不支持的架构 %s", arch_value)
            return None

        assets: list[dict[str, Any]] = data.get("assets", [])
        for asset in assets:
            if asset.get("name") == target:
                url: str | None = asset.get("browser_download_url")
                if url:
                    return url
        logger.warning("Zen: 未找到 asset %s", target)
        return None
