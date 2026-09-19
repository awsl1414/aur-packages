"""QQ Linux 版本解析器：rule-deb 规则定位 URL + GetSign 签名钩子。

各架构安装包 URL 由 ``parser_config.url`` 的 jmespath 规则从 pcConfig 响应
提取（``字段.deb || 字段`` 兼容 dict 与裸字符串两种形态）；版本号经
``DebControlVersionMixin`` 从 deb 文件头部 control 段统一提取。下载前经
im.qq.com GetSign 换取带 sign 的临时链接——鉴权是业务逻辑，留在专属类
而非规则引擎。
"""

import json
import logging

import httpx

from aur_metadata.config import HttpConfig, QQConfig
from aur_metadata.constants import ArchEnum

from .rule import RuleDebParser

logger = logging.getLogger(__name__)


class QQParser(RuleDebParser):
    """QQ Linux 版本解析器：URL 规则化提取 + deb 头部版本 + GetSign 签名

    ``parser_config.url`` 按架构配置 pcConfig 的 jmespath 提取规则；
    ``resolve_raw_url`` 对原始链接签名（签名链接会过期，仅内部下载使用）。
    """

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
