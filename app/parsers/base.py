"""解析器基类模块"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from app.constants import ArchEnum

logger = logging.getLogger(__name__)

# 结构变更日志附带响应片段的截断长度（字符），防止大响应刷屏
_STRUCTURE_SNIPPET_MAX_LENGTH: int = 300


class BaseParser(ABC):
    """解析器抽象基类，定义版本号和 URL 解析接口。

    子类需要实现的契约：

    - ``parse_version``：从 API/页面响应中提取语义化版本号
    - ``parse_url``：提取**未加工的下载 URL**——会原样写入 PKGBUILD 的
      ``source_<arch>=()`` 字段。对需要鉴权/签名的下载（如 QQ GetSign），
      只能返回原始 URL，签名动作放在内部下载流程中处理
    - ``resolve_raw_url``（默认原样返回）：把原始 URL 转为**可直接下载的 URL**，
      仅用于程序内部下载和计算校验和。子类可重写为 async 以实现额外处理，
      例如 QQ 走 im.qq.com 的 GetSign 换取带 sign 的临时链接

    JSON 解析复用 ``_parse_json_dict``：按 ``response_data`` 身份缓存解析结果，
    使一次采集周期内 parse_version + 各架构 parse_url 只解析一次（trae manifest
    较大时收益明显）。子类自定义 ``__init__`` 时须调 ``super().__init__()``。

    结构性校验失败（期望的字段/列表/条目缺失或形态不符）统一走
    ``_log_structure_change`` 打日志，便于跨 parser 检索上游改版事件。

    安装包文件自带权威版本元数据的解析器（deb 等）不适用上述 ``parse_version``
    契约，应继承 ``PackageFileVersionParser``：版本经服务层下载安装包头部后由
    ``version_from_package_head`` 提取。
    """

    def __init__(self) -> None:
        # 本次响应的解析缓存：按 response_data 身份键控
        self._cached_response: str | None = None
        self._cached_data: dict[str, Any] | None = None

    @staticmethod
    def _arch_value(arch: ArchEnum | str) -> str:
        """将 ArchEnum 或 str 统一为架构字符串值"""
        return arch.value if isinstance(arch, ArchEnum) else arch

    def _log_structure_change(self, detail: str, evidence: Any) -> None:
        """统一记录「疑似上游数据结构变更」告警。

        响应内容偏离 parser 预期结构时调用——通常是上游 API/页面改版。
        统一格式（解析器名 + 详情 + 响应片段）便于日志检索与快速定位上游
        实际返回的内容。``evidence`` 取最贴近失配点的数据（完整响应或
        子对象），非字符串先 repr；值校验失败（如版本号不一致）与配置
        错误（如不支持的架构）不属结构变更，走普通 logger。
        """
        snippet: str = (evidence if isinstance(evidence, str) else repr(evidence))[
            :_STRUCTURE_SNIPPET_MAX_LENGTH
        ]
        logger.warning(
            "疑似上游结构变更 [%s] %s；响应片段: %s",
            type(self).__name__,
            detail,
            snippet,
        )

    def _json_section(self, response_data: str, *keys: str) -> dict[str, Any] | None:
        """按路径取嵌套 dict 段（如 ``data.manifest.linux``）。

        任一级缺失或非 dict 返回 None 并记结构变更日志，统一各 parser
        的嵌套导航写法（dict 内容属上游真实可变边界，守卫有必要）。
        """
        data: dict[str, Any] | None = self._parse_json_dict(response_data)
        if data is None:
            return None
        section: Any = data
        for key in keys:
            if not isinstance(section, dict):
                break
            section = section.get(key)
        if isinstance(section, dict):
            return section
        self._log_structure_change(f"响应缺少 {'.'.join(keys)} 段", data)
        return None

    def _arch_key(self, arch: ArchEnum | str, mapping: dict[str, str]) -> str | None:
        """架构 → 映射表 key 查找；不支持的架构记普通警告并返回 None。

        不支持的架构是配置/调用错误而非上游结构变更，故走普通日志；
        与 trae/zen/qq 三处的映射查找保持同一行为与格式。
        """
        arch_value: str = self._arch_value(arch)
        key: str | None = mapping.get(arch_value)
        if key is None:
            logger.warning("%s: 不支持的架构 %s", type(self).__name__, arch_value)
        return key

    def _parse_json_dict(self, response_data: str) -> dict[str, Any] | None:
        """解析 JSON 响应为 dict 并按 ``response_data`` 缓存。

        非 dict 结构或解析失败返回 None。``response_data`` 由调用方
        （PackageService.collect_version）保证为 fetch_text 的 str 结果，
        无需类型守卫。同一响应在一次采集周期内会被 parse_version 与
        各架构 parse_url 反复使用，缓存使其只解析一次；跨周期 fetcher
        返回新的字符串对象，缓存自然失效。
        """
        if response_data is self._cached_response:
            return self._cached_data
        try:
            data: Any = json.loads(response_data)
        except json.JSONDecodeError:
            self._log_structure_change("响应非合法 JSON", response_data)
            self._cached_response, self._cached_data = response_data, None
            return None
        result: dict[str, Any] | None = data if isinstance(data, dict) else None
        self._cached_response, self._cached_data = response_data, result
        return result

    @abstractmethod
    def parse_version(self, response_data: str) -> str | None:
        """从响应数据中提取版本号"""

    @abstractmethod
    def parse_url(self, arch: ArchEnum | str, response_data: str) -> str | None:
        """从响应数据中提取原始下载 URL（写入 PKGBUILD 的 ``source_<arch>=()``）。

        返回值必须是未经签名/鉴权处理的原始 URL——这样 PKGBUILD 静态可见，
        由内部下载流程在需要时完成动态签名处理。
        """

    async def resolve_raw_url(self, arch: ArchEnum | str, raw_url: str) -> str | None:
        """将 ``parse_url`` 产出的原始 URL 转为可直接下载的 URL（程序内部使用）。

        默认原样返回；子类可重写以附加鉴权/签名处理，例如 QQ 对 deb 链接
        走 im.qq.com GetSign 换取带 sign 的临时链接。

        下载路径与版本源响应解耦：hash 采集从已持久化的原始 URL 出发，
        无需重取版本源响应数据。
        """
        return raw_url

    def get_request_headers(self) -> dict[str, str] | None:
        """返回抓取本 parser 数据源时使用的完整请求头。

        设计契约：**完整替换** ``Fetcher.DEFAULT_HEADERS``，不与任何默认头
        合并。返回的字典必须自包含所有需要发送的 header（``User-Agent``、
        ``Accept`` 等通用字段由 parser 自己负责，Fetcher 不会自动补齐）。
        返回 ``None`` 表示使用 ``Fetcher.DEFAULT_HEADERS`` 即可。

        典型用例：QQ 的 CDN 要求 ``Origin``/``Referer`` 指向 im.qq.com 并
        携带 Chrome Client Hints（``sec-ch-ua-*``、``sec-fetch-*``）才会
        返回数据。Fetcher 不预置这些特殊头，由本方法按需提供。
        """
        return None


class PackageFileVersionParser(BaseParser):
    """安装包文件版本解析器基类：版本号从安装包文件本身提取。

    适用场景：安装包（deb 等）自带权威版本元数据，比在文件名/页面上做正则
    稳健。采集流程由 ``PackageService.collect_version`` 按类型检测（isinstance）
    切换到「下载安装包头部 → ``version_from_package_head``」路径，**不走**
    ``parse_version``。

    安装包 URL 有两种来源，子类按需选择：

    - 静态配置：重写 ``package_download_urls`` 返回 arch→URL 映射
      （如 DebParser，``parser_config.urls`` 注入），版本域无需版本源响应；
    - 动态定位：默认实现返回 ``None``，服务层先 ``fetch_text`` 版本源响应、
      再逐架构 ``parse_url`` 定位安装包 URL（如 QQ 的 pcConfig）。

    拿到 URL 后统一走 ``resolve_raw_url``（鉴权/签名钩子）下载头部。
    """

    # 版本提取所需读取的安装包文件头部最大字节数，服务层据此流式下载。
    # deb 的 control 段恒在文件头部（实测通常 <64KB），留出余量取 256KB
    PACKAGE_HEAD_MAX_BYTES: int = 256 * 1024

    def package_download_urls(self) -> dict[str, str] | None:
        """静态配置的各架构安装包 URL（arch_value → 原始 URL，未鉴权）。

        返回 ``None`` 表示无静态配置，由服务层经版本源响应 + ``parse_url``
        动态定位（见类 docstring）。
        """
        return None

    @abstractmethod
    def version_from_package_head(self, head: bytes) -> str | None:
        """从安装包文件头部字节提取版本号；结构不符返回 None 并记结构变更日志"""

    def parse_version(self, response_data: str) -> str | None:
        """版本不来自文本响应，恒返回 None（实际提取走 ``version_from_package_head``）"""
        return None
