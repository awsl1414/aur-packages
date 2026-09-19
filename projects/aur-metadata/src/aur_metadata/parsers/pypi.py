"""PyPI 包解析器

从 PyPI JSON API 提取最新版本号与 sdist 下载 URL。纯 Python 包为 ``arch=any``，
sdist 与架构无关——``parse_url`` 对任意 arch 返回同一 sdist URL。
"""

from typing import Any

from aur_metadata.constants import ArchEnum

from .base import BaseParser


class PyPIParser(BaseParser):
    """PyPI 包解析器：``info.version`` 取版本，``urls[]`` 中 sdist 取 URL"""

    def parse_version(self, response_data: str) -> str | None:
        """从 PyPI JSON 的 ``info.version`` 提取版本号。

        ``info`` 键存在但值为 null（限流/错误载荷）时 ``get("info", {})``
        默认值不生效，须显式判 dict，否则 ``None.get`` 抛 AttributeError。
        """
        data: dict[str, Any] | None = self._parse_json_dict(response_data)
        if data is None:
            return None
        info: Any = data.get("info")
        version: str | None = info.get("version") if isinstance(info, dict) else None
        if not version:
            self._log_structure_change("缺少 info.version 字段", data)
            return None
        return version

    def parse_url(self, arch: ArchEnum | str, response_data: str) -> str | None:
        """从 ``urls[]`` 中取 ``packagetype=="sdist"`` 的下载链接"""
        data: dict[str, Any] | None = self._parse_json_dict(response_data)
        if data is None:
            return None
        # urls 为 null 时 get 默认值不生效，须判 list（同 info: null 一类）
        urls: Any = data.get("urls")
        if not isinstance(urls, list):
            self._log_structure_change("缺少 urls 列表", data)
            return None
        for url_info in urls:
            if url_info.get("packagetype") == "sdist":
                download_url: str | None = url_info.get("url")
                if download_url:
                    return download_url
        self._log_structure_change("urls[] 中无 sdist 下载项", data)
        return None
