"""Zen Browser 每夜版解析器"""

import json
import logging
import re
from typing import Any

from constants.constants import ArchEnum

from .base_parser import BaseParser

logger = logging.getLogger(__name__)

# ArchEnum 值到 GitHub Release asset 名称的映射
ARCH_ASSET_MAP: dict[str, str] = {
    ArchEnum.X86_64.value: "zen.linux-x86_64.tar.xz",
    ArchEnum.AARCH64.value: "zen.linux-aarch64.tar.xz",
}


class ZenParser(BaseParser):
    """Zen Browser 每夜版解析器

    从 GitHub Releases API 获取 twilight-1 标签的发布信息。
    twilight-1 是固定标签，发布内容每天更新。

    API 端点: https://api.github.com/repos/zen-browser/desktop/releases/tags/twilight-1
    """

    VERSION_PATTERN: re.Pattern[str] = re.compile(r"(\d+\.\d+[a-z]?)")

    def parse_version(self, response_data: str | Any) -> str | None:
        """从 GitHub Release 的 name 字段提取版本号

        release name 格式: "Twilight build - 1.20t (2026-05-16 at 02:13:41)"
        提取结果: "1.20t"
        """
        if not isinstance(response_data, str):
            return None

        try:
            data: dict[str, Any] = json.loads(response_data)
        except json.JSONDecodeError:
            logger.warning("Zen Browser: JSON 解析失败")
            return None

        release_name: str | None = data.get("name")
        if not release_name:
            logger.warning("Zen Browser: Release 缺少 name 字段")
            return None

        match: re.Match[str] | None = self.VERSION_PATTERN.search(release_name)
        if not match:
            logger.warning(
                "Zen Browser: 无法从 release name 提取版本: %s", release_name
            )
            return None

        return match.group(1)

    def parse_url(self, arch: ArchEnum | str, response_data: str | Any) -> str | None:
        """从 GitHub Release assets 中提取指定架构的下载 URL"""
        if not isinstance(response_data, str):
            return None

        try:
            data: dict[str, Any] = json.loads(response_data)
        except json.JSONDecodeError:
            return None

        arch_value = self._arch_value(arch)
        target_asset_name: str | None = ARCH_ASSET_MAP.get(arch_value)
        if not target_asset_name:
            return None

        assets: list[dict[str, Any]] = data.get("assets", [])
        for asset in assets:
            if asset.get("name") == target_asset_name:
                return asset.get("browser_download_url")

        logger.warning(
            "Zen Browser: 未找到 %s 架构的 asset: %s", arch_value, target_asset_name
        )
        return None
