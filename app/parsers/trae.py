"""Trae IDE 版本解析器

解析 ``data.manifest.linux``：``version`` 取版本号；``download[]`` 中按 ``region``
匹配项取各架构 tarball 链接。region 走 ``parser_config`` 注入（cn/sg/va 等），
国际版与国内版仅 ``fetch_url`` 与 region 取值不同。
"""

import logging
from typing import Any

from app.constants import ArchEnum

from .base import BaseParser

logger = logging.getLogger(__name__)

# 架构到 download 项内链接 key 的映射
_ARCH_KEY_MAP: dict[str, str] = {
    ArchEnum.X86_64.value: "x64.tar.gz",
    ArchEnum.AARCH64.value: "arm64.tar.gz",
}


class TraeParser(BaseParser):
    """Trae IDE 版本解析器：JSON manifest 提取版本号与按 region 选链"""

    def __init__(self, region: str = "cn") -> None:
        super().__init__()
        self._region = region

    def parse_version(self, response_data: str | Any) -> str | None:
        """从 ``data.manifest.linux.version`` 提取版本号"""
        linux = self._linux_manifest(response_data)
        if linux is None:
            return None
        version: str | None = linux.get("version")
        if not version:
            logger.warning("Trae: manifest.linux 缺少 version")
            return None
        return version

    def parse_url(self, arch: ArchEnum | str, response_data: str | Any) -> str | None:
        """按 ``region`` 在 ``download[]`` 中匹配项取指定架构链接"""
        linux = self._linux_manifest(response_data)
        if linux is None:
            return None

        arch_value = self._arch_value(arch)
        url_key: str | None = _ARCH_KEY_MAP.get(arch_value)
        if url_key is None:
            logger.warning("Trae: 不支持的架构 %s", arch_value)
            return None

        download: Any = linux.get("download")
        if not isinstance(download, list):
            logger.warning("Trae: manifest.linux.download 非列表")
            return None
        for entry in download:
            if isinstance(entry, dict) and entry.get("region") == self._region:
                url: str | None = entry.get(url_key)
                if url:
                    return url
        logger.warning(
            "Trae: download[] 中无 region=%s 的 %s 链接", self._region, url_key
        )
        return None

    def _linux_manifest(self, response_data: str | Any) -> dict[str, Any] | None:
        """返回 ``data.manifest.linux`` 字典；结构不符返回 None。

        JSON 解析复用 BaseParser._parse_json_dict 的缓存，避免版本与各架构
        URL 解析重复解析同一 manifest。
        """
        if not isinstance(response_data, str):
            return None
        data: dict[str, Any] | None = self._parse_json_dict(response_data)
        if data is None:
            return None
        try:
            linux: Any = data["data"]["manifest"]["linux"]
        except (KeyError, TypeError):
            logger.warning("Trae: 响应缺少 data.manifest.linux")
            return None
        return linux if isinstance(linux, dict) else None
