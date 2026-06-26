"""QQ Linux 版本解析器"""

import json
import logging
import re
from typing import Any

from constants.constants import ArchEnum

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class QQParser(BaseParser):
    """QQ Linux 版本解析器"""

    def _extract_json(self, response_data: str) -> dict[str, Any] | None:
        """从 JavaScript 响应中提取并解析 JSON 配置"""
        pattern: str = r"var params\s*=\s*(\{.*?\});"
        matched: re.Match[str] | None = re.search(pattern, response_data, re.DOTALL)
        if not matched:
            return None
        try:
            return json.loads(matched.group(1))
        except json.JSONDecodeError:
            logger.warning("JSON解析失败: %.200s...", matched.group(1))
            return None

    def _get_deb_url(self, result: dict[str, Any], arch_value: str) -> str | None:
        """从已解析的 JSON 中获取指定架构的 deb 下载 URL"""
        match arch_value:
            case ArchEnum.X86_64.value:
                return result.get("x64DownloadUrl", {}).get("deb")
            case ArchEnum.AARCH64.value:
                return result.get("armDownloadUrl", {}).get("deb")
            case ArchEnum.LOONG64.value:
                loongarch_url: str | dict[str, str] | None = result.get(
                    "loongarchDownloadUrl"
                )
                if isinstance(loongarch_url, dict):
                    return loongarch_url.get("deb")
                return loongarch_url
            case ArchEnum.MIPS64EL.value:
                mips_url: str | dict[str, str] | None = result.get("mipsDownloadUrl")
                if isinstance(mips_url, dict):
                    return mips_url.get("deb")
                return mips_url
        return None

    def parse_version(self, response_data: str | Any) -> str | None:
        """从 QQ 响应数据中提取版本号（含构建号），并交叉验证 API 与 URL 版本"""
        if not isinstance(response_data, str):
            return None

        result: dict[str, Any] | None = self._extract_json(response_data)
        if not result:
            return None

        # 从 API 字段获取基础版本号
        api_version: str | None = result.get("version")
        if not api_version:
            logger.warning("QQ API 响应缺少 version 字段")
            return None

        # 从 deb URL 提取完整版本信息
        url: str | None = self._get_deb_url(result, ArchEnum.X86_64.value)
        if not url:
            return None

        url_pattern: str = r"QQ_([\d.]+)_(\d+)_amd64"
        url_match: re.Match[str] | None = re.search(url_pattern, url)
        if not url_match:
            return None

        url_base_version: str = url_match.group(1)
        build_number: str = url_match.group(2)

        # 交叉验证：API 版本必须与 URL 基础版本一致
        if url_base_version != api_version:
            logger.warning(
                "QQ 版本不匹配: API=%s, URL=%s", api_version, url_base_version
            )
            return None

        return f"{api_version}_{build_number}"

    def parse_url(self, arch: ArchEnum | str, response_data: str | Any) -> str | None:
        """从 QQ 响应数据中提取指定架构的下载 URL"""
        if not isinstance(response_data, str):
            return None

        result: dict[str, Any] | None = self._extract_json(response_data)
        if not result:
            return None

        arch_value = self._arch_value(arch)
        return self._get_deb_url(result, arch_value)
