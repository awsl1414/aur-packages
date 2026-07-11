"""包注册表模块"""

from dataclasses import dataclass

from app.constants import ArchEnum
from app.parsers.base import BaseParser


@dataclass(frozen=True)
class PackageEntry:
    """单个包的注册信息"""

    name: str
    parser: BaseParser
    fetch_url: str
    archs: list[ArchEnum]


class PackageRegistry:
    """包注册表：管理所有可查询的包。

    新增包只需在应用启动时调用 ``register``，无需修改路由——
    通用查询接口 ``GET /api/packages/{name}`` 会自动覆盖。
    """

    def __init__(self) -> None:
        self._entries: dict[str, PackageEntry] = {}

    def register(self, entry: PackageEntry) -> None:
        """注册一个包。重名注册将覆盖旧条目。"""
        self._entries[entry.name] = entry

    def get(self, name: str) -> PackageEntry | None:
        """按名称查找包，不存在返回 None"""
        return self._entries.get(name)

    def list_all(self) -> list[PackageEntry]:
        """返回所有已注册包"""
        return list(self._entries.values())
