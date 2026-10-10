"""QQ Linux 版本解析器：rule-deb 规则定位 URL + GetSign 签名钩子。

各架构安装包 URL 由 ``parser_config.url`` 的 jmespath 规则从 pcConfig 响应
提取（``字段.deb || 字段`` 兼容 dict 与裸字符串两种形态）；版本号经
``DebControlVersionMixin`` 从 deb 文件头部 control 段统一提取。下载前经
im.qq.com GetSign 换取带 sign 的临时链接——鉴权是业务逻辑，留在专属类
而非规则引擎。
"""

import json
import logging
import time
from typing import Any

import httpx

from aur_metadata.config import AppConfig, HttpConfig, QQConfig
from aur_metadata.constants import ArchEnum

from .rule import RuleDebParser

logger = logging.getLogger(__name__)

# 签名链接复用窗口（秒）：保守取 30 分钟——远短于链接实际有效期，但足以让
# 同包轮询查询与同次采集（版本域 + hash 域各 resolve 一次）命中缓存，
# 不再放大对 im.qq.com 的签名 RPC
_SIGN_TTL_SECONDS: float = 1800


class QQParser(RuleDebParser):
    """QQ Linux 版本解析器：URL 规则化提取 + deb 头部版本 + GetSign 签名

    ``parser_config.url`` 按架构配置 pcConfig 的 jmespath 提取规则；
    ``resolve_raw_url`` 对原始链接签名（签名链接会过期，供内部下载与查询
    接口 download_urls 实时生成使用，urls 字段仍暴露原始链接）。
    """

    def __init__(
        self,
        app_config: AppConfig,
        version: dict[str, Any] | None = None,
        url: dict[str, dict[str, Any] | str] | None = None,
    ) -> None:
        super().__init__(app_config, version, url)
        # 签名结果 TTL 缓存：raw_url → (signed_url, 过期时刻 monotonic)。
        # 实例由 registry 持有直至 reload，缓存随实例生命周期自然失效
        self._sign_cache: dict[str, tuple[str, float]] = {}

    async def _sign_url(self, url: str) -> str | None:
        """对指定 deb 链接换取带 sign 的临时链接（TTL 内复用，见模块常量）。

        流程：
        1) 请求 im.qq.com/index/ 获取 tgw_l7_route cookie
        2) 调用 GetSign RPC 传入原始 URL，获取带 sign 的临时下载链接
        """
        cached = self._sign_cache.get(url)
        if cached is not None and cached[1] > time.monotonic():
            return cached[0]

        signed = await self._request_signed_url(url)
        if signed is not None:
            self._sign_cache[url] = (signed, time.monotonic() + _SIGN_TTL_SECONDS)
        return signed

    async def _request_signed_url(self, url: str) -> str | None:
        """实际执行签名 RPC；任何失败记日志返回 None（签名是附加能力，不拖垮采集）"""
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
        供内部下载与查询接口 ``download_urls`` 字段实时生成使用。签名链接
        会过期：禁止落库，对外 ``urls`` 字段始终为 parse_url 的原始 URL
        （PKGBUILD 经 DLAGENT 在 makepkg 阶段自行完成签名）。
        """
        return await self._sign_url(raw_url)
