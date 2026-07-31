"""从 DB 加载包配置，构建内存中的包注册表"""

import json
import logging

from app.constants import ArchEnum
from app.models import Package
from app.parsers.registry import get_parser
from app.registry import PackageEntry, PackageRegistry

logger = logging.getLogger(__name__)


async def load_registry_from_db() -> tuple[PackageRegistry, dict[str, int], list[Package]]:
    """加载所有 enabled 包，构建注册表、name→id 映射与有效包列表。

    name→id 映射供调度器按包 id 注册 schedule，避免每次查库。返回的有效包列表
    供调度同步复用，避免 reload 再查一次库。

    单行脏数据（未知 parser_type、非法 archs）只记 warning 跳过，不致整体失败——
    否则一行配置错误会让 reload 返 500，或在 lifespan 让整个应用启动失败。
    """
    pkgs: list[Package] = await Package.filter(enabled=True)
    entries: list[PackageEntry] = []
    name_to_id: dict[str, int] = {}
    valid_pkgs: list[Package] = []
    for p in pkgs:
        try:
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
            valid_pkgs.append(p)
        except Exception:
            logger.warning("跳过坏配置行 id=%s name=%s", p.id, p.name, exc_info=True)
            continue

    registry: PackageRegistry = PackageRegistry()
    registry.replace_all(entries)
    return registry, name_to_id, valid_pkgs
