"""Navicat Premium 版本解析器

版本号从 Navicat 官网 release-note HTML 页面正则提取；下载 URL 不在页面响应里，
而是固定的 AppImage 直链，因此通过 ``parser_config.urls``（arch→URL 映射）注入。
"""

import logging
import re
from typing import Any

from app.constants import ArchEnum

from .base import BaseParser

logger = logging.getLogger(__name__)


class NavicatParser(BaseParser):
    """Navicat Premium CS 版本解析器：HTML 版本 + 配置注入 URL"""

    def __init__(self, urls: dict[str, str] | None = None) -> None:
        super().__init__()
        self._urls = urls or {}

    def parse_version(self, response_data: str | Any) -> str | None:
        """从 release-note HTML 中提取 ``Navicat ... (Linux) ... version X.Y.Z``"""
        if not isinstance(response_data, str):
            return None
        pattern: str = r"(Navicat[^()]*\(Linux\)[^v]*version[^\d]*)(\d+\.\d+\.\d+)"
        matched: re.Match[str] | None = re.search(pattern, response_data, re.IGNORECASE)
        if not matched:
            logger.warning("Navicat: HTML 中未匹配到 Linux 版本号")
            return None
        return matched.group(2)

    def parse_url(self, arch: ArchEnum | str, response_data: str | Any) -> str | None:
        """从配置注入的 arch→URL 映射中取下载链接（与响应无关）"""
        arch_value = self._arch_value(arch)
        url: str | None = self._urls.get(arch_value)
        if not url:
            logger.warning("Navicat: parser_config.urls 中无 %s 架构链接", arch_value)
        return url
