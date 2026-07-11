"""QQ Linux 版本解析器"""

import json
import logging
import re
from typing import Any

import httpx

from constants.constants import (
    DEFAULT_TIMEOUT,
    USER_AGENT,
    ArchEnum,
)

from .base_parser import BaseParser

logger = logging.getLogger(__name__)

# URL 签名服务常量
COOKIE_URL = "https://im.qq.com/index/"
SIGN_URL = (
    "https://im.qq.com/http2rpc/gotrpc/noauth/trpc.qqntv2.urlsign.UrlSign/GetSign"
)


class QQParser(BaseParser):
    """QQ Linux 版本解析器"""

    def _parse_response(self, response_data: str) -> dict[str, Any] | None:
        """解析 JSON 响应；解析失败返回 None"""
        try:
            data = json.loads(response_data)
        except json.JSONDecodeError:
            logger.warning("QQ 响应 JSON 解析失败: %.200s...", response_data)
            return None
        if not isinstance(data, dict):
            return None
        return data

    def _get_deb_url(
        self, linux_section: dict[str, Any], arch_value: str
    ) -> str | None:
        """从已解析的 Linux 段中获取指定架构的 deb 下载 URL"""
        match arch_value:
            case ArchEnum.X86_64.value:
                urls = linux_section.get("x64DownloadUrl")
                if isinstance(urls, dict):
                    return urls.get("deb")
                return None
            case ArchEnum.AARCH64.value:
                urls = linux_section.get("armDownloadUrl")
                if isinstance(urls, dict):
                    return urls.get("deb")
                return None
            case ArchEnum.LOONG64.value:
                loongarch_url = linux_section.get("loongarchDownloadUrl")
                if isinstance(loongarch_url, dict):
                    return loongarch_url.get("deb")
                return loongarch_url if isinstance(loongarch_url, str) else None
            case ArchEnum.MIPS64EL.value:
                mips_url = linux_section.get("mipsDownloadUrl")
                if isinstance(mips_url, dict):
                    return mips_url.get("deb")
                return mips_url if isinstance(mips_url, str) else None
        return None

    def parse_version(self, response_data: str | Any) -> str | None:
        """从 QQ 响应数据中提取版本号（含构建号），并交叉验证 API 与 URL 版本。

        步骤：
        1. 校验输入为 JSON 字符串且含 ``Linux`` 段
        2. 读取 API 字段 ``Linux.version``（基础版本号）
        3. 从 x86_64 的 deb URL 提取 build number（URL 必须含 ``_amd64``）
        4. 交叉验证：API 版本必须与 URL 中的版本号一致（防 API/资源脱节）
        5. 拼接为 ``<api_version>_<build_number>`` 形式返回
        """
        if not isinstance(response_data, str):
            return None

        data = self._parse_response(response_data)
        if not data:
            return None

        linux_section = data.get("Linux")
        if not isinstance(linux_section, dict):
            logger.warning("QQ 响应缺少 Linux 段")
            return None

        # 从 API 字段获取基础版本号
        api_version: str | None = linux_section.get("version")
        if not api_version:
            logger.warning("QQ API 响应缺少 Linux.version 字段")
            return None

        # 从 deb URL 提取完整版本信息
        url: str | None = self._get_deb_url(linux_section, ArchEnum.X86_64.value)
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
        """从 QQ 响应数据中提取指定架构的下载 URL（原始未签名链接）"""
        if not isinstance(response_data, str):
            return None

        data = self._parse_response(response_data)
        if not data:
            return None

        linux_section = data.get("Linux")
        if not isinstance(linux_section, dict):
            return None

        arch_value = self._arch_value(arch)
        return self._get_deb_url(linux_section, arch_value)

    def _sign_url(self, url: str) -> str | None:
        """对指定 deb 链接换取带 sign 的临时链接。

        流程：
        1) 请求 im.qq.com/index/ 获取 tgw_l7_route cookie
        2) 调用 GetSign RPC 传入原始 URL，获取带 sign 的临时下载链接
        """
        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
                # 1) 从 im.qq.com/index/ 抓取 tgw_l7_route cookie
                cookie_resp = client.get(
                    COOKIE_URL, headers={"User-Agent": USER_AGENT}
                )
                cookie_resp.raise_for_status()
                cookie: str | None = cookie_resp.cookies.get("tgw_l7_route")
                if not cookie:
                    logger.error("无法从 %s 获取 tgw_l7_route cookie", COOKIE_URL)
                    return None

                # 2) 调用 GetSign 换取带 sign 的下载链接
                sign_resp = client.post(
                    SIGN_URL,
                    headers={
                        "User-Agent": USER_AGENT,
                        "Content-Type": "application/json",
                        "Origin": "https://im.qq.com",
                        "Referer": "https://im.qq.com/index/",
                        "x-oidb": '{"uint32_command":"0x9b8e","uint32_service_type":1}',
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

    def resolve_url(self, arch: ArchEnum | str, response_data: str | Any) -> str | None:
        """获取可直接下载的 URL（QQ 需对 URL 签名以通过 GetSign 鉴权）。

        返回的 URL 已带 sign 查询参数，可直接用于 aria2c 等下载器；
        写入 PKGBUILD 的 source 字段应使用 parse_url 的原始 URL，
        由 DLAGENTS 在构建时调用 linuxqq-get-url.sh 完成签名。
        """
        url = self.parse_url(arch, response_data)
        if not url:
            return None
        return self._sign_url(url)
