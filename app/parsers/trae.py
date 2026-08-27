"""Trae IDE 版本解析器

解析 ``data.manifest.linux``：``download[]`` 中按 ``region`` 匹配项取各架构
tarball 链接。上游 manifest 已无独立版本字段，版本号内嵌于链接路径
``.../releases/stable/<version>/...``，是唯一版本来源（各 region 版本一致）。
region 走 ``parser_config`` 注入（cn/sg/va 等），国际版与国内版仅 ``fetch_url``
与 region 取值不同。
"""

import re
from typing import Any

from app.constants import ArchEnum

from .base import BaseParser

# 架构到 download 项内链接 key 的映射
_ARCH_KEY_MAP: dict[str, str] = {
    ArchEnum.X86_64.value: "x64.tar.gz",
    ArchEnum.AARCH64.value: "arm64.tar.gz",
}

# 下载链接内嵌版本段，如 .../releases/stable/2.3.77497/linux/...；
# 不要求尾斜杠——版本段为路径最后一段时同样可提取
_VERSION_URL_PATTERN: re.Pattern[str] = re.compile(r"/releases/stable/([^/]+)")


class TraeParser(BaseParser):
    """Trae IDE 版本解析器：JSON manifest 提取版本号与按 region 选链"""

    def __init__(self, region: str = "cn") -> None:
        super().__init__()
        self._region = region

    def parse_version(self, response_data: str) -> str | None:
        """从 region 项各架构链接提取版本号并校验一致。

        只扫 ``_ARCH_KEY_MAP`` 的架构链接 key（而非 entry 全部值，防未来
        新增的字符串字段误命中版本段）；各架构版本不一致说明上游部分发布，
        拒绝返回——否则 hash 会挂到与 URL 不符的版本号下。
        """
        linux: dict[str, Any] | None = self._json_section(
            response_data, "data", "manifest", "linux"
        )
        if linux is None:
            return None
        entry: dict[str, Any] | None = self._region_entry(linux)
        if entry is None:
            return None

        versions: set[str] = set()
        for url_key in _ARCH_KEY_MAP.values():
            url: Any = entry.get(url_key)
            if isinstance(url, str) and (match := _VERSION_URL_PATTERN.search(url)):
                versions.add(match.group(1))

        if not versions:
            self._log_structure_change(
                "download 链接中无版本段（releases/stable/<version>）", entry
            )
            return None
        if len(versions) > 1:
            self._log_structure_change(
                f"各架构链接版本不一致: {sorted(versions)}", entry
            )
            return None
        return versions.pop()

    def parse_url(self, arch: ArchEnum | str, response_data: str) -> str | None:
        """从 region 项取指定架构链接"""
        linux: dict[str, Any] | None = self._json_section(
            response_data, "data", "manifest", "linux"
        )
        if linux is None:
            return None

        url_key: str | None = self._arch_key(arch, _ARCH_KEY_MAP)
        if url_key is None:
            return None

        entry: dict[str, Any] | None = self._region_entry(linux)
        if entry is None:
            return None
        url: str | None = entry.get(url_key)
        if url:
            return url
        self._log_structure_change(
            f"region={self._region} 项中无 {url_key} 链接", entry
        )
        return None

    def _region_entry(self, linux: dict[str, Any]) -> dict[str, Any] | None:
        """返回 ``download[]`` 中 ``region`` 匹配项；非列表或无匹配返回 None"""
        download: Any = linux.get("download")
        if not isinstance(download, list):
            self._log_structure_change("manifest.linux.download 非列表", linux)
            return None
        for entry in download:
            if isinstance(entry, dict) and entry.get("region") == self._region:
                return entry
        self._log_structure_change(f"download[] 中无 region={self._region} 项", linux)
        return None
