"""QQ Linux 版本解析器

数据源：第三方聚合 API（``http://ip.llz.asia:8000``）。

API 直接返回 ``version``、各架构 ``urls`` 和 ``hashes``，无需走 im.qq.com
的 GetSign 签名流程——原始 URL 即可直接下载，签名动作由 PKGBUILD 的
DLAGENTS 在 makepkg 阶段独立完成。

响应格式::

    {
      "code": 0,
      "message": "ok",
      "data": {
        "name": "qq",
        "version": "3.2.31_260710",
        "urls": {
          "x86_64":  "https://qqdl.gtimg.cn/.../QQ_..._amd64_01.deb",
          "aarch64": "https://qqdl.gtimg.cn/.../QQ_..._arm64_01.deb",
          "loong64": "https://qqdl.gtimg.cn/.../QQ_..._loongarch64_01.deb"
        },
        "hashes": {
          "x86_64":  "<b2sum hex>",
          "aarch64": "<b2sum hex>",
          "loong64": "<b2sum hex>"
        }
      }
    }
"""

import json
import logging
from typing import Any

from constants.constants import ArchEnum

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class QQParser(BaseParser):
    """QQ Linux 版本解析器（第三方聚合 API 数据源）"""

    def _parse_response(self, response_data: str | Any) -> dict[str, Any] | None:
        """解析 JSON 响应并返回 ``data`` 段；结构不符返回 None"""
        if not isinstance(response_data, str):
            return None
        try:
            data = json.loads(response_data)
        except json.JSONDecodeError:
            logger.warning("QQ 响应 JSON 解析失败: %.200s...", response_data)
            return None
        if not isinstance(data, dict):
            return None
        if data.get("code") != 0:
            logger.warning("QQ API 返回非 0 code: %r", data.get("code"))
            return None
        inner = data.get("data")
        if not isinstance(inner, dict):
            logger.warning("QQ API 响应缺少 data 段")
            return None
        return inner

    def parse_version(self, response_data: str | Any) -> str | None:
        """从 QQ 聚合 API 响应中提取版本号（``data.version``）"""
        data = self._parse_response(response_data)
        if not data:
            return None
        version: str | None = data.get("version")
        if not version:
            logger.warning("QQ API 响应缺少 data.version 字段")
            return None
        return version

    def parse_url(self, arch: ArchEnum | str, response_data: str | Any) -> str | None:
        """从 QQ 聚合 API 响应中提取指定架构的下载 URL（原始未签名链接）"""
        data = self._parse_response(response_data)
        if not data:
            return None
        urls = data.get("urls")
        if not isinstance(urls, dict):
            logger.warning("QQ API 响应缺少 data.urls 字段")
            return None
        arch_value = self._arch_value(arch)
        url: str | None = urls.get(arch_value)
        if not url:
            logger.warning("QQ API 响应中无 %s 架构的 URL", arch_value)
        return url

    def parse_hashes(
        self, response_data: str | Any, archs: list[ArchEnum]
    ) -> dict[str, str] | None:
        """从 QQ 聚合 API 响应中提取各架构的 b2 校验和"""
        data = self._parse_response(response_data)
        if not data:
            return None
        hashes = data.get("hashes")
        if not isinstance(hashes, dict):
            logger.warning("QQ API 响应缺少 data.hashes 字段，回退到下载流程")
            return None
        result: dict[str, str] = {}
        for arch in archs:
            arch_value = arch.value
            checksum = hashes.get(arch_value)
            if isinstance(checksum, str) and checksum:
                result[arch_value] = checksum
            else:
                logger.warning("QQ API 响应中无 %s 架构的 hash", arch_value)
        return result if result else None
