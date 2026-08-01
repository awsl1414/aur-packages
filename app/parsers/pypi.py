"""PyPI 包解析器

从 PyPI JSON API 提取最新版本号与 sdist 下载 URL。纯 Python 包为 ``arch=any``，
sdist 与架构无关——``parse_url`` 对任意 arch 返回同一 sdist URL。
"""

import logging
from typing import Any

from app.constants import ArchEnum

from .base import BaseParser

logger = logging.getLogger(__name__)


class PyPIParser(BaseParser):
    """PyPI 包解析器：``info.version`` 取版本，``urls[]`` 中 sdist 取 URL"""

    def parse_version(self, response_data: str | Any) -> str | None:
        """从 PyPI JSON 的 ``info.version`` 提取版本号"""
        if not isinstance(response_data, str):
            return None
        data: dict[str, Any] | None = self._parse_json_dict(response_data)
        if data is None:
            return None
        version: str | None = data.get("info", {}).get("version")
        if not version:
            logger.warning("PyPI: 缺少 info.version 字段")
            return None
        return version

    def parse_url(self, arch: ArchEnum | str, response_data: str | Any) -> str | None:
        """从 ``urls[]`` 中取 ``packagetype=="sdist"`` 的下载链接"""
        if not isinstance(response_data, str):
            return None
        data: dict[str, Any] | None = self._parse_json_dict(response_data)
        if data is None:
            return None
        urls: list[dict[str, Any]] = data.get("urls", [])
        for url_info in urls:
            if url_info.get("packagetype") == "sdist":
                download_url: str | None = url_info.get("url")
                if download_url:
                    return download_url
        logger.warning("PyPI: 未找到 sdist 下载 URL")
        return None
