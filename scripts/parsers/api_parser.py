"""helper API 统一响应解析器（唯一解析器）

数据源：``aur-packages-helper`` 项目的 ``GET /api/v1/packages/{name}`` 接口。
所有上游（QQ / Navicat / Trae / Zen / PyPI）的源解析均在 helper 服务端完成，
客户端只消费统一 JSON 结构::

    {
      "code": 0,
      "message": "ok",
      "data": {
        "name": "qq",
        "version": "3.2.31_260710",
        "urls":  { "<arch>": "<原始未签名下载 URL>" },
        "hashes": { "<arch>": "<checksum hex or null>" }
      }
    }

``urls`` 为写入 PKGBUILD ``source_<arch>=()`` 的原始链接（如 QQ 的未签名 deb
链接，签名动作由 PKGBUILD 的 DLAGENTS 在 makepkg 阶段独立完成）。
``hashes`` 由 helper 服务端计算，可能为空或缺部分架构——此时由
``PackageUpdater`` 回退到按 ``urls`` 下载 + 本地计算。
"""

import json
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParsedPackage:
    """helper API 解析结果。

    - ``version``：语义化版本号
    - ``urls``：``{arch_value: 原始未签名 URL}``，写入 PKGBUILD ``source_<arch>=()``
    - ``hashes``：``{arch_value: checksum}``，已过滤掉 None/空值；可能为空字典，
      表示 helper 未提供 hash，由调用方回退到本地下载计算
    """

    version: str
    urls: dict[str, str]
    hashes: dict[str, str]


class ApiParser:
    """helper API 统一响应解析器。

    一次 ``parse`` 返回完整的 ``ParsedPackage``，避免版本/URL/hash 分别解析时
    重复解码同一响应。
    """

    def parse(self, response_data: str) -> ParsedPackage | None:
        """解析 helper API 响应为 ``ParsedPackage``；结构不符返回 None。"""
        data = self._parse_response(response_data)
        if data is None:
            return None

        version = data.get("version")
        if not isinstance(version, str) or not version:
            logger.warning("API 响应缺少有效的 data.version 字段")
            return None

        urls_raw = data.get("urls")
        if not isinstance(urls_raw, dict):
            logger.warning("API 响应缺少 data.urls 字段")
            return None
        urls: dict[str, str] = {
            arch: url
            for arch, url in urls_raw.items()
            if isinstance(arch, str) and isinstance(url, str) and url
        }
        if not urls:
            logger.warning("API 响应 data.urls 中无有效架构 URL")
            return None

        hashes: dict[str, str] = {}
        hashes_raw = data.get("hashes")
        if isinstance(hashes_raw, dict):
            for arch, checksum in hashes_raw.items():
                if isinstance(arch, str) and isinstance(checksum, str) and checksum:
                    hashes[arch] = checksum
        # hashes 可能为空（helper 未提供）→ 调用方回退本地计算，不视为解析失败

        return ParsedPackage(version=version, urls=urls, hashes=hashes)

    @staticmethod
    def _parse_response(response_data: str) -> dict[str, Any] | None:
        """解析 JSON 响应并返回 ``data`` 段；结构不符返回 None。"""
        if not isinstance(response_data, str):
            return None
        try:
            data: Any = json.loads(response_data)
        except json.JSONDecodeError:
            logger.warning("API 响应 JSON 解析失败: %.200s...", response_data)
            return None
        if not isinstance(data, dict):
            return None
        if data.get("code") != 0:
            logger.warning("API 返回非 0 code: %r", data.get("code"))
            return None
        inner: Any = data.get("data")
        if not isinstance(inner, dict):
            logger.warning("API 响应缺少 data 段")
            return None
        return inner
