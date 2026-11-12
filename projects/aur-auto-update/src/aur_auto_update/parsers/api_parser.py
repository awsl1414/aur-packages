"""metadata API 统一响应解析器（唯一解析器）

数据源：``aur-metadata`` 项目的 ``GET /api/v1/packages/{name}`` 接口。
所有上游（QQ / Navicat / Trae / Zen / PyPI）的源解析均在 metadata 服务端完成，
客户端只消费统一 JSON 结构::

    {
      "code": 0,
      "message": "ok",
      "data": {
        "name": "qq",
        "version": "3.2.31_260710",
        "urls":          { "<arch>": "<原始未签名下载 URL>" },
        "download_urls": { "<arch>": "<实时可下载 URL or null>" },
        "hashes":        { "<arch>": "<checksum hex or null>" }
      }
    }

``urls`` 为写入 PKGBUILD ``source_<arch>=()`` 的原始链接（如 QQ 的未签名 deb
链接，签名动作由 PKGBUILD 的 DLAGENTS 在 makepkg 阶段独立完成）。
``download_urls`` 为 metadata 服务端查询时实时生成的可直接下载链接（如 QQ 经
GetSign 签名的临时链接，会过期；值为 null 表示该架构签名失败），仅供客户端
回退下载使用，禁止写入 PKGBUILD。
``hashes`` 由 metadata 服务端计算，可能为空或缺部分架构——此时由
``PackageUpdater`` 按 ``download_urls``（缺失回退 ``urls``）下载 + 本地计算。
"""

import json
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParsedPackage:
    """metadata API 解析结果。

    - ``version``：语义化版本号
    - ``urls``：``{arch_value: 原始未签名 URL}``，写入 PKGBUILD ``source_<arch>=()``
    - ``hashes``：``{arch_value: checksum}``，已过滤掉 None/空值；可能为空字典，
      表示 metadata 未提供 hash，由调用方回退到本地下载计算
    - ``download_urls``：``{arch_value: 实时可下载 URL}``，已过滤掉 None/空值；
      回退下载路径优先使用（QQ 等鉴权源必需），为空字典时回退 ``urls``
    """

    version: str
    urls: dict[str, str]
    hashes: dict[str, str]
    download_urls: dict[str, str]


class ApiParser:
    """metadata API 统一响应解析器。

    一次 ``parse`` 返回完整的 ``ParsedPackage``，避免版本/URL/hash 分别解析时
    重复解码同一响应。
    """

    @staticmethod
    def _clean_str_dict(raw: Any) -> dict[str, str]:
        """过滤 ``{arch: value}`` 中键/值非字符串或值为空的条目。"""
        if not isinstance(raw, dict):
            return {}
        return {
            arch: value
            for arch, value in raw.items()
            if isinstance(arch, str) and isinstance(value, str) and value
        }

    def parse(self, response_data: str) -> ParsedPackage | None:
        """解析 metadata API 响应为 ``ParsedPackage``；结构不符返回 None。"""
        data = self._parse_response(response_data)
        if data is None:
            return None

        version = data.get("version")
        if not isinstance(version, str) or not version:
            logger.warning("API 响应缺少有效的 data.version 字段")
            return None

        urls = self._clean_str_dict(data.get("urls"))
        if not urls:
            logger.warning("API 响应 data.urls 中无有效架构 URL")
            return None

        # hashes 可能为空（metadata 未提供）→ 调用方回退本地计算，不视为解析失败
        hashes = self._clean_str_dict(data.get("hashes"))

        download_urls_raw = data.get("download_urls")
        if not isinstance(download_urls_raw, dict):
            logger.warning("API 响应缺少 data.download_urls 字段")
            return None
        download_urls = self._clean_str_dict(download_urls_raw)

        return ParsedPackage(
            version=version,
            urls=urls,
            hashes=hashes,
            download_urls=download_urls,
        )

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
