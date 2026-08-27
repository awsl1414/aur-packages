"""Zen Browser 每夜版解析器

从 GitHub Releases API 的固定标签 ``twilight-1``（发布内容每天更新）提取版本号与
各架构 asset 链接。release ``name`` 形如 ``"Twilight build - 1.22t (2026-08-01 at ...)"``，
版本号由「数字.数字[字母]」片段拼上括号内日期（去连字符）得到，如 ``1.22t.20260801``。
"""

import re
from typing import Any

from app.constants import ArchEnum

from .base import BaseParser

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

    def parse_version(self, response_data: str) -> str | None:
        """从 release ``name`` 提取版本号，有日期则拼为 ``version.YYYYMMDD``"""
        data: dict[str, Any] | None = self._parse_json_dict(response_data)
        if data is None:
            return None
        release_name: str | None = data.get("name")
        if not release_name:
            self._log_structure_change("Release 缺少 name 字段", data)
            return None
        version_match: re.Match[str] | None = self._VERSION_PATTERN.search(release_name)
        if not version_match:
            self._log_structure_change(
                f"无法从 release name 提取版本号: {release_name}", data
            )
            return None
        version: str = version_match.group(0)
        date_match: re.Match[str] | None = self._DATE_PATTERN.search(release_name)
        if date_match is None:
            return version
        year, month, day = date_match.group(1), date_match.group(2), date_match.group(3)
        return f"{version}.{year}{month}{day}"

    def parse_url(self, arch: ArchEnum | str, response_data: str) -> str | None:
        """从 ``assets[]`` 中按名称匹配指定架构的 ``browser_download_url``"""
        data: dict[str, Any] | None = self._parse_json_dict(response_data)
        if data is None:
            return None

        target: str | None = self._arch_key(arch, _ARCH_ASSET_MAP)
        if target is None:
            return None

        # assets 为 null 时 get 默认值不生效，须判 list（同 info: null 一类）
        assets: Any = data.get("assets")
        if not isinstance(assets, list):
            self._log_structure_change("缺少 assets 列表", data)
            return None
        for asset in assets:
            if asset.get("name") == target:
                url: str | None = asset.get("browser_download_url")
                if url:
                    return url
        self._log_structure_change(f"assets[] 中未找到 {target}", data)
        return None
