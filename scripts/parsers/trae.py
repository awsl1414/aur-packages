"""Trae IDE 版本解析器"""

import json
from enum import Enum
from typing import Any

from constants.constants import ArchEnum

from .base_parser import BaseParser

# 架构到 API 响应中下载链接 key 的映射
ARCH_KEY_MAP: dict[str, str] = {
    ArchEnum.X86_64.value: "x64.tar.gz",
    ArchEnum.AARCH64.value: "arm64.tar.gz",
}


class TraeRegion(Enum):
    """Trae CDN 地域"""

    CN = "cn"
    SG = "sg"
    US = "va"


class TraeParser(BaseParser):
    """Trae IDE 版本解析器，从 JSON API 提取版本号和下载链接"""

    def __init__(self, region: TraeRegion = TraeRegion.CN) -> None:
        self._region = region

    def _parse_linux_manifest(self, response_data: str | Any) -> dict[str, Any] | None:
        """解析响应，返回 data.data.manifest.linux 字典；非法输入或结构缺失返回 None"""
        if not isinstance(response_data, str):
            return None
        try:
            return json.loads(response_data)["data"]["manifest"]["linux"]
        except (KeyError, TypeError, json.JSONDecodeError):
            return None

    def parse_version(self, response_data: str | Any) -> str | None:
        linux = self._parse_linux_manifest(response_data)
        if linux is None:
            return None
        try:
            return linux["version"]
        except (KeyError, TypeError):
            return None

    def parse_url(self, arch: ArchEnum | str, response_data: str | Any) -> str | None:
        linux = self._parse_linux_manifest(response_data)
        if linux is None:
            return None

        arch_value = self._arch_value(arch)
        url_key = ARCH_KEY_MAP.get(arch_value)
        if not url_key:
            return None

        try:
            for entry in linux["download"]:
                if entry.get("region") == self._region.value:
                    return entry[url_key]
            return None
        except (KeyError, TypeError, IndexError):
            return None
