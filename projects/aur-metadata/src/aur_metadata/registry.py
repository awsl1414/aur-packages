"""包注册表模块"""

from dataclasses import dataclass

from aur_metadata.constants import ArchEnum
from aur_metadata.parsers.base import BaseParser


@dataclass(frozen=True)
class PackageEntry:
    """单个包的注册信息"""

    name: str
    parser: BaseParser
    fetch_url: str
    archs: list[ArchEnum]


class PackageRegistry:
    """包注册表：内存中的可查询包集合，由 DB 加载（replace_all）构建。

    新增/修改包只需操作 ``packages`` 表并调用 reload，无需改路由——
    通用查询接口 ``GET /api/packages/{name}`` 会自动覆盖。
    """

    def __init__(self) -> None:
        self._entries: dict[str, PackageEntry] = {}

    def replace_all(self, entries: list[PackageEntry]) -> None:
        """用给定列表整体替换注册表内容（用于从 DB 重新加载）"""
        self._entries = {entry.name: entry for entry in entries}

    def get(self, name: str) -> PackageEntry | None:
        """按名称查找包，不存在返回 None"""
        return self._entries.get(name)

    def list_all(self) -> list[PackageEntry]:
        """返回所有已注册包"""
        return list(self._entries.values())
