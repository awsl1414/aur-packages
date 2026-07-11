"""解析器基类模块"""

from abc import ABC, abstractmethod
from typing import Any

from constants.constants import ArchEnum


class BaseParser(ABC):
    """解析器抽象基类，定义版本号、URL 和哈希解析接口。

    子类需要实现的契约：

    - ``parse_version``：从 API/页面响应中提取语义化版本号
    - ``parse_url``：提取**写入 PKGBUILD ``source_<arch>=()`` 的原始 URL**。
      对需要鉴权/签名的下载（如 QQ GetSign），返回未签名原始链接，
      签名动作由 PKGBUILD 的 DLAGENTS 在 makepkg 阶段完成
    - ``resolve_url``（默认委托给 ``parse_url``）：返回**可直接下载的 URL**，
      仅用于程序内部下载和计算校验和。子类可重写以实现额外处理
    - ``parse_hashes``（默认返回 None）：返回 API 直接提供的校验和字典，
      避免本地下载重算。返回 None 时由 PackageUpdater 走下载流程
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
        由 DLAGENTS 在 ``makepkg`` 阶段调用专用脚本完成动态处理。
        """

    def resolve_url(self, arch: ArchEnum | str, response_data: str | Any) -> str | None:
        """获取可直接用于下载的 URL（程序内部使用，不写入 PKGBUILD）。

        默认实现：直接返回 ``parse_url`` 的结果。子类可重写以实现额外处理，
        例如 QQ 包通过外部脚本对 URL 签名后返回带 sign 的临时链接。
        """
        return self.parse_url(arch, response_data)

    def parse_hashes(
        self, response_data: str | Any, archs: list[ArchEnum]
    ) -> dict[str, str] | None:
        """从响应数据中提取各架构的校验和（可选）。

        返回 ``{arch_value: checksum}`` 字典。返回 ``None`` 表示 parser 不
        提供 hash，由 ``PackageUpdater`` 走下载文件 + 本地计算 hash 的流程。

        典型用例：QQ 的第三方聚合 API 直接返回 b2sums，无需本地下载即可
        写入 PKGBUILD，省去下载几百 MB deb 包的开销。
        """
        return None
