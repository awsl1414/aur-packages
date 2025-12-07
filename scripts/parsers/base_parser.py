from abc import ABC, abstractmethod
from typing import Any


class Parser(ABC):
    """
    版本抽象基类
    """

    @abstractmethod
    def parse_version(self, response_data: dict[str, Any]) -> str | None:
        """
        解析响应数据，提取版本号

        Args:
            response_data: API响应数据

        Returns:
            版本号字符串，如果解析失败则返回None
        """
        pass

    @abstractmethod
    def parse_deb_url(self, arch: str, response_data: dict[str, Any]) -> str | None:
        """
        解析响应数据，提取 deb 包 URL

        Args:
            response_data: API响应数据

        Returns:
            deb 包 URL 字符串，如果解析失败则返回None
        """
        pass
