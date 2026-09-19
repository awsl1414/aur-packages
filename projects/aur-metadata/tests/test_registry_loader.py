"""aur_metadata.services.registry_loader 集成测试（DB）。"""

from __future__ import annotations

from aur_metadata.services.registry_loader import load_registry_from_db
from tests.fakes import make_app_config

_APP_CONFIG = make_app_config()


async def test_loads_valid_packages(db, make_package) -> None:
    await make_package(name="qq", parser_type="qq")
    await make_package(name="wechat", parser_type="qq", archs='["x86_64"]')

    registry, pkgs = await load_registry_from_db(_APP_CONFIG)
    assert registry.get("qq") is not None
    assert registry.get("wechat") is not None
    assert {p.name for p in pkgs} == {"qq", "wechat"}
