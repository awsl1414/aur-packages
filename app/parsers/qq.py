"""QQ Linux 版本解析器"""

import json
import logging
import re
from typing import Any

import httpx

from app.constants import DEFAULT_TIMEOUT, USER_AGENT, ArchEnum
from app.constants.qq import (
    QQ_COOKIE_URL,
    QQ_OIDB_COMMAND,
    QQ_OIDB_SERVICE_TYPE,
    QQ_ORIGIN,
    QQ_SIGN_URL,
)

from .base import BaseParser

logger = logging.getLogger(__name__)

# 架构到 Linux 段下载字段名的映射
_ARCH_FIELD_MAP: dict[str, str] = {
    ArchEnum.X86_64.value: "x64DownloadUrl",
    ArchEnum.AARCH64.value: "armDownloadUrl",
    ArchEnum.LOONG64.value: "loongarchDownloadUrl",
    ArchEnum.MIPS64EL.value: "mipsDownloadUrl",
}


class QQParser(BaseParser):
    """QQ Linux 版本解析器：URL 需经 im.qq.com GetSign 签名方可下载"""

    def _get_deb_url(
        self, linux_section: dict[str, Any], arch_value: str
    ) -> str | None:
        """取指定架构的 deb 下载 URL；字段值为 dict 取 ``deb`` 键，为裸字符串直接用。

        归一化后强制 str 校验并落结构变更日志——非字符串值（如嵌套 dict）
        若放行，会在 parse_version 的 re.search 抛 TypeError 逃逸采集流程，
        或作为垃圾 URL 流入签名/下载环节。
        """
        field: str | None = _ARCH_FIELD_MAP.get(arch_value)
        if field is None:
            return None
        value: Any = linux_section.get(field)
        url: Any = value.get("deb") if isinstance(value, dict) else value
        if isinstance(url, str) and url:
            return url
        self._log_structure_change(
            f"{field} 值非预期形态（期望 dict 含 deb 字符串或裸字符串 URL）",
            linux_section,
        )
        return None

    def parse_version(self, response_data: str) -> str | None:
        """从 QQ 响应数据中提取版本号（含构建号），并交叉验证 API 与 URL 版本。

        步骤：
        1. 读取 API 字段 ``Linux.version``（基础版本号）
        2. 从 x86_64 的 deb URL 提取 build number（URL 必须含 ``_amd64``）
        3. 交叉验证：API 版本必须与 URL 中的版本号一致（防 API/资源脱节）
        4. 拼接为 ``<api_version>_<build_number>`` 形式返回
        """
        linux_section: dict[str, Any] | None = self._json_section(
            response_data, "Linux"
        )
        if linux_section is None:
            return None

        # 从 API 字段获取基础版本号
        api_version: str | None = linux_section.get("version")
        if not api_version:
            self._log_structure_change("缺少 Linux.version 字段", linux_section)
            return None

        # 从 deb URL 提取完整版本信息（形态异常已由 _get_deb_url 记结构日志）
        url: str | None = self._get_deb_url(linux_section, ArchEnum.X86_64.value)
        if not url:
            return None

        url_match: re.Match[str] | None = re.search(r"QQ_([\d.]+)_(\d+)_amd64", url)
        if not url_match:
            self._log_structure_change(
                "x64 deb URL 不含 QQ_<version>_<build>_amd64 模式", url
            )
            return None
        url_base_version, build_number = url_match.group(1), url_match.group(2)

        # 交叉验证：API 版本必须与 URL 基础版本一致
        # （值不一致属资源脱节而非结构变更，走普通日志）
        if url_base_version != api_version:
            logger.warning(
                "QQ 版本不匹配: API=%s, URL=%s", api_version, url_base_version
            )
            return None

        return f"{api_version}_{build_number}"

    def parse_url(self, arch: ArchEnum | str, response_data: str) -> str | None:
        """从 QQ 响应数据中提取指定架构的下载 URL（原始未签名链接）"""
        linux_section: dict[str, Any] | None = self._json_section(
            response_data, "Linux"
        )
        if linux_section is None:
            return None
        arch_value: str = self._arch_value(arch)
        field: str | None = self._arch_key(arch_value, _ARCH_FIELD_MAP)
        if field is None:
            return None
        return self._get_deb_url(linux_section, arch_value)

    async def _sign_url(self, url: str) -> str | None:
        """对指定 deb 链接换取带 sign 的临时链接。

        流程：
        1) 请求 im.qq.com/index/ 获取 tgw_l7_route cookie
        2) 调用 GetSign RPC 传入原始 URL，获取带 sign 的临时下载链接
        """
        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                # 1) 从 im.qq.com/index/ 抓取 tgw_l7_route cookie
                cookie_resp = await client.get(
                    QQ_COOKIE_URL, headers={"User-Agent": USER_AGENT}
                )
                cookie_resp.raise_for_status()
                cookie: str | None = cookie_resp.cookies.get("tgw_l7_route")
                if not cookie:
                    logger.error("无法从 %s 获取 tgw_l7_route cookie", QQ_COOKIE_URL)
                    return None

                # 2) 调用 GetSign 换取带 sign 的下载链接
                sign_resp = await client.post(
                    QQ_SIGN_URL,
                    headers={
                        "User-Agent": USER_AGENT,
                        "Content-Type": "application/json",
                        "Origin": QQ_ORIGIN,
                        "Referer": QQ_COOKIE_URL,
                        "x-oidb": f'{{"uint32_command":"{QQ_OIDB_COMMAND}","uint32_service_type":{QQ_OIDB_SERVICE_TYPE}}}',
                    },
                    cookies={"tgw_l7_route": cookie},
                    json={"url": url},
                )
                sign_resp.raise_for_status()
                data = sign_resp.json()
                if not isinstance(data, dict):
                    logger.error("GetSign 返回非字典结构")
                    return None
                inner = data.get("data")
                if not isinstance(inner, dict):
                    logger.error("GetSign 返回结果中无 data 字段")
                    return None
                signed_url: str | None = inner.get("url")
                if not signed_url:
                    logger.error("GetSign 返回结果中无 data.url")
                    return None
                return signed_url
        except httpx.HTTPError as e:
            logger.error("QQ URL 签名网络错误: %s", e)
            return None
        except (json.JSONDecodeError, ValueError) as e:
            logger.error("QQ URL 签名响应解析失败: %s", e)
            return None

    async def resolve_raw_url(self, arch: ArchEnum | str, raw_url: str) -> str | None:
        """对原始 deb 链接签名，返回带 sign 的可直接下载 URL（QQ 鉴权）。

        返回的 URL 已带 sign 查询参数，可直接用于流式下载并计算校验和；
        对外 API 暴露的应使用 parse_url 的原始 URL（签名链接会过期）。
        """
        return await self._sign_url(raw_url)
