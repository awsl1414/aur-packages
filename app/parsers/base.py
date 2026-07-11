"""解析器基类模块"""

from abc import ABC, abstractmethod
from typing import Any

from app.constants import ArchEnum


class BaseParser(ABC):
    """解析器抽象基类，定义版本号和 URL 解析接口。

    子类需要实现的契约：

    - ``parse_version``：从 API/页面响应中提取语义化版本号
    - ``parse_url``：提取**未加工的下载 URL**——会原样写入 PKGBUILD 的
      ``source_<arch>=()`` 字段。对需要鉴权/签名的下载（如 QQ GetSign），
      只能返回原始 URL，签名动作放在内部下载流程中处理
    - ``resolve_url``（默认委托给 ``parse_url``）：返回**可直接下载的 URL**，
      仅用于程序内部下载和计算校验和。子类可重写为 async 以实现额外处理，
      例如 QQ 走 im.qq.com 的 GetSign 换取带 sign 的临时链接
    """

    @staticmethod
    def _arch_value(arch: ArchEnum | str) -> str:
        """将 ArchEnum 或 str 统一为架构字符串值"""
        return arch.value if isinstance(arch, ArchEnum) else arch

    @abstractmethod
    def parse_version(self, response_data: str | Any) -> str | None:
        """从响应数据中提取版本号"""

    @abstractmethod
    def parse_url(self, arch: ArchEnum | str, response_data: str | Any) -> str | None:
        """从响应数据中提取原始下载 URL（写入 PKGBUILD 的 ``source_<arch>=()``）。

        返回值必须是未经签名/鉴权处理的原始 URL——这样 PKGBUILD 静态可见，
        由内部下载流程在需要时完成动态签名处理。
        """

    async def resolve_url(
        self, arch: ArchEnum | str, response_data: str | Any
    ) -> str | None:
        """获取可直接用于下载的 URL（程序内部使用，不写入 PKGBUILD）。

        默认实现：直接返回 ``parse_url`` 的结果。子类可重写为 async 以实现
        额外处理，例如 QQ 包通过 im.qq.com 的 GetSign 对 URL 签名后返回
        带 sign 的临时链接。
        """
        return self.parse_url(arch, response_data)

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
