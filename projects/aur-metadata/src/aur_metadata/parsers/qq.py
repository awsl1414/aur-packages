"""QQ Linux 版本解析器

版本号经 ``DebControlVersionMixin`` 从 deb 文件头部 control 段统一提取
（替代早期「API version + 文件名 build 正则」双源拼接方案）；安装包 URL
来自 pcConfig 响应，须再经 im.qq.com GetSign 签名方可下载。
"""

import json
import logging
from typing import Any

import httpx

from aur_metadata.config import HttpConfig, QQConfig
from aur_metadata.constants import ArchEnum

from .deb import DebControlVersionMixin

logger = logging.getLogger(__name__)

# 架构到 Linux 段下载字段名的映射
_ARCH_FIELD_MAP: dict[str, str] = {
    ArchEnum.X86_64.value: "x64DownloadUrl",
    ArchEnum.AARCH64.value: "armDownloadUrl",
    ArchEnum.LOONG64.value: "loongarchDownloadUrl",
    ArchEnum.MIPS64EL.value: "mipsDownloadUrl",
}


class QQParser(DebControlVersionMixin):
    """QQ Linux 版本解析器：版本取自 deb control 段，URL 需 GetSign 签名

    安装包 URL 无静态配置（``package_download_urls`` 保持默认 ``None``），
    服务层先 ``fetch_text`` pcConfig 响应再逐架构 ``parse_url`` 定位。
    """

    def _get_deb_url(
        self, linux_section: dict[str, Any], arch_value: str
    ) -> str | None:
        """取指定架构的 deb 下载 URL；字段值为 dict 取 ``deb`` 键，为裸字符串直接用。

        归一化后强制 str 校验并落结构变更日志——非字符串值（如嵌套 dict）
        若放行，会作为垃圾 URL 流入签名/下载环节。
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
            http: HttpConfig = self._app_config.http
            qq: QQConfig = self._app_config.qq
            async with httpx.AsyncClient(timeout=http.default_timeout) as client:
                # 1) 从 im.qq.com/index/ 抓取 tgw_l7_route cookie
                cookie_resp = await client.get(
                    qq.cookie_url, headers={"User-Agent": http.user_agent}
                )
                cookie_resp.raise_for_status()
                cookie: str | None = cookie_resp.cookies.get("tgw_l7_route")
                if not cookie:
                    logger.error("无法从 %s 获取 tgw_l7_route cookie", qq.cookie_url)
                    return None

                # 2) 调用 GetSign 换取带 sign 的下载链接
                sign_resp = await client.post(
                    qq.sign_url,
                    headers={
                        "User-Agent": http.user_agent,
                        "Content-Type": "application/json",
                        "Origin": qq.origin,
                        "Referer": qq.cookie_url,
                        "x-oidb": (
                            f'{{"uint32_command":"{qq.oidb_command}",'
                            f'"uint32_service_type":{qq.oidb_service_type}}}'
                        ),
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
