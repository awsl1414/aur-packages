"""解析器基类模块"""

from abc import ABC, abstractmethod
from typing import Any

from constants.constants import ArchEnum


class BaseParser(ABC):
    """解析器抽象基类，定义版本号和 URL 解析接口"""

    @staticmethod
    def _arch_value(arch: ArchEnum | str) -> str:
        """将 ArchEnum 或 str 统一为架构字符串值"""
        return arch.value if isinstance(arch, ArchEnum) else arch

    @abstractmethod
    def parse_version(self, response_data: str | Any) -> str | None:
        """从响应数据中提取版本号"""

    @abstractmethod
    def parse_url(self, arch: ArchEnum | str, response_data: str | Any) -> str | None:
        """从响应数据中提取下载 URL"""
