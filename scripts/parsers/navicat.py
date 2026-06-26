"""Navicat Premium 版本解析器"""

import re
from typing import Any

from constants.constants import ArchEnum

from .base_parser import BaseParser


class NavicatPremiumCSParser(BaseParser):
    """Navicat Premium CS 版本解析器"""

    def __init__(self, urls: dict[str, str] | None = None) -> None:
        self._urls = urls or {}

    def parse_version(self, response_data: str | Any) -> str | None:
        """从 Navicat 响应数据中提取版本号"""
        if not isinstance(response_data, str):
            return None
        pattern: str = r"(Navicat[^()]*\(Linux\)[^v]*version[^\d]*)(\d+\.\d+\.\d+)"
        matched: re.Match[str] | None = re.search(pattern, response_data, re.IGNORECASE)
        return matched.group(2) if matched else None

    def parse_url(self, arch: ArchEnum | str, response_data: str | Any) -> str | None:
        """从配置注入的 URL 映射中获取下载链接"""
        arch_value = self._arch_value(arch)
        return self._urls.get(arch_value)
