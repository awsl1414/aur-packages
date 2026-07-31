"""从 DB 加载包配置，构建内存中的包注册表"""

import json

from app.constants import ArchEnum
from app.models import Package
from app.parsers.registry import get_parser
from app.registry import PackageEntry, PackageRegistry


async def load_registry_from_db() -> tuple[PackageRegistry, dict[str, int]]:
    """加载所有 enabled 包，构建注册表与 name→id 映射。

    name→id 映射供调度器按包 id 注册 schedule，避免每次查库。
    """
    pkgs: list[Package] = await Package.filter(enabled=True)
    entries: list[PackageEntry] = []
    name_to_id: dict[str, int] = {}
    for p in pkgs:
        archs: list[ArchEnum] = [ArchEnum(a) for a in json.loads(p.archs)]
        entries.append(
            PackageEntry(
                name=p.name,
                parser=get_parser(p.parser_type),
                fetch_url=p.fetch_url,
                archs=archs,
            )
        )
        name_to_id[p.name] = p.id

    registry: PackageRegistry = PackageRegistry()
    registry.replace_all(entries)
    return registry, name_to_id
