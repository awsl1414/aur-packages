"""从 DB 加载包配置，构建内存中的包注册表"""

import json
import logging
from typing import Any

from app.constants import ArchEnum
from app.models import Package
from app.parsers.registry import get_parser
from app.registry import PackageEntry, PackageRegistry

logger = logging.getLogger(__name__)


async def load_registry_from_db() -> tuple[PackageRegistry, list[Package]]:
    """加载所有 enabled 包，构建注册表与有效包列表。

    返回的有效包列表供调度器注册 schedule 与 reload 同步复用，避免重复查库。

    单行脏数据（未知 parser_type、非法 archs）只记 warning 跳过，不致整体失败——
    否则一行配置错误会让 reload 返 500，或在 lifespan 让整个应用启动失败。
    """
    pkgs: list[Package] = await Package.filter(enabled=True)
    entries: list[PackageEntry] = []
    valid_pkgs: list[Package] = []
    for p in pkgs:
        try:
            archs: list[ArchEnum] = [ArchEnum(a) for a in json.loads(p.archs)]
            # parser_config 为 JSON 字符串（可空），透传给 parser 构造函数
            parser_config: dict[str, Any] = (
                json.loads(p.parser_config) if p.parser_config else {}
            )
            entries.append(
                PackageEntry(
                    name=p.name,
                    parser=get_parser(p.parser_type, parser_config),
                    fetch_url=p.fetch_url,
                    archs=archs,
                )
            )
            valid_pkgs.append(p)
        except Exception:
            logger.warning("跳过坏配置行 id=%s name=%s", p.id, p.name, exc_info=True)
            continue

    registry: PackageRegistry = PackageRegistry()
    registry.replace_all(entries)
    return registry, valid_pkgs
