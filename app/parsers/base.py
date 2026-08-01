"""解析器基类模块"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from app.constants import ArchEnum

logger = logging.getLogger(__name__)


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
    """

    def __init__(self) -> None:
        # 本次响应的解析缓存：按 response_data 身份键控
        self._cached_response: str | None = None
        self._cached_data: dict[str, Any] | None = None

    @staticmethod
    def _arch_value(arch: ArchEnum | str) -> str:
        """将 ArchEnum 或 str 统一为架构字符串值"""
        return arch.value if isinstance(arch, ArchEnum) else arch

    def _parse_json_dict(self, response_data: str) -> dict[str, Any] | None:
        """解析 JSON 响应为 dict 并按 ``response_data`` 缓存；非字典或解析失败返回 None。

        同一响应在一次采集周期内会被 parse_version 与各架构 parse_url 反复使用，
        缓存使其只解析一次。跨周期 fetcher 返回新的字符串对象，缓存自然失效。
        """
        if response_data is self._cached_response:
            return self._cached_data
        try:
            data: Any = json.loads(response_data)
        except json.JSONDecodeError:
            logger.warning("%s: JSON 解析失败", type(self).__name__)
            self._cached_response, self._cached_data = response_data, None
            return None
        result: dict[str, Any] | None = data if isinstance(data, dict) else None
        self._cached_response, self._cached_data = response_data, result
        return result

    @abstractmethod
    def parse_version(self, response_data: str | Any) -> str | None:
        """从响应数据中提取版本号"""

    @abstractmethod
    def parse_url(self, arch: ArchEnum | str, response_data: str | Any) -> str | None:
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
