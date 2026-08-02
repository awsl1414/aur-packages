"""Zen Browser 每夜版解析器

从 GitHub Releases API 的固定标签 ``twilight-1``（发布内容每天更新）提取版本号与
各架构 asset 链接。release ``name`` 形如 ``"Twilight build - 1.22t (2026-08-01 at ...)"``，
版本号由「数字.数字[字母]」片段拼上括号内日期（去连字符）得到，如 ``1.22t.20260801``。
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

    # release name 内版本号片段，如 "1.22t" / "1.5a"
    _VERSION_PATTERN: re.Pattern[str] = re.compile(r"\d+\.\d+[a-z]?")
    # release name 括号内日期，如 "2026-08-01"
    _DATE_PATTERN: re.Pattern[str] = re.compile(r"\((\d{4})-(\d{2})-(\d{2})")

    def parse_version(self, response_data: str | Any) -> str | None:
        """从 release ``name`` 提取版本号，有日期则拼为 ``version.YYYYMMDD``"""
        if not isinstance(response_data, str):
            return None
        data: dict[str, Any] | None = self._parse_json_dict(response_data)
        if data is None:
            return None
        release_name: str | None = data.get("name")
        if not release_name:
            logger.warning("Zen: Release 缺少 name 字段")
            return None
        version_match: re.Match[str] | None = self._VERSION_PATTERN.search(release_name)
        if not version_match:
            logger.warning("Zen: 无法从 release name 提取版本号: %s", release_name)
            return None
        version: str = version_match.group(0)
        date_match: re.Match[str] | None = self._DATE_PATTERN.search(release_name)
        if date_match is None:
            return version
        year, month, day = date_match.group(1), date_match.group(2), date_match.group(3)
        return f"{version}.{year}{month}{day}"

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
