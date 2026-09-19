"""共享测试夹具。

约定：
- DB 夹具用临时文件 SQLite + ``Tortoise.generate_schemas``，函数级隔离；
  不复用生产 ``init_db``（其依赖 schema.sql 的 STRICT/视图，对 ORM 单测无必要）。
- 可控桩（FakeParser/FakeFetcher）见 ``tests/fakes.py``。
"""

from __future__ import annotations

import json
import os
from collections.abc import AsyncGenerator, Callable, Coroutine
from pathlib import Path
from typing import Any

import pytest
from tortoise import Tortoise

from aur_metadata.models import Package

# ─────────────────────────────────────────────────────────────────────────────
# 环境夹具
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def _clean_config_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """清除配置相关环境变量，隔离宿主机环境对默认路径解析测试的影响"""
    monkeypatch.delenv("APP_CONFIG", raising=False)
    monkeypatch.delenv("APP_PACKAGES", raising=False)
    assert os.environ.get("APP_CONFIG") is None


# ─────────────────────────────────────────────────────────────────────────────
# DB 夹具
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
async def db(tmp_path: Path) -> AsyncGenerator[None]:
    """函数级 Tortoise 初始化（临时文件 SQLite），自动建表与清理。"""
    db_url: str = f"sqlite://{tmp_path / 'test.db'}"
    await Tortoise.init(
        db_url=db_url,
        modules={"models": ["aur_metadata.models"]},
        _enable_global_fallback=True,
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest.fixture
def make_package() -> Callable[..., Coroutine[Any, Any, Package]]:
    """创建一行 packages 配置的工厂夹具。"""

    async def _make(**overrides: Any) -> Package:
        defaults: dict[str, Any] = {
            "name": "qq",
            "parser_type": "qq",
            "fetch_url": "https://example.com/config.json",
            "archs": '["x86_64","aarch64","loong64"]',
            "enabled": True,
            "schedule_type": "interval",
            "interval_seconds": 3600,
        }
        defaults.update(overrides)
        return await Package.create(**defaults)

    return _make


# ─────────────────────────────────────────────────────────────────────────────
# QQ 样例数据
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def qq_response() -> str:
    """构造一份合法的 QQ pcConfig 响应（版本/URL 一致，含三架构 deb）。"""
    return json.dumps(
        {
            "Linux": {
                "version": "3.2.29",
                "x64DownloadUrl": {
                    "deb": "https://qqdl.gtimg.cn/QQ_3.2.29_260528_amd64_01.deb"
                },
                "armDownloadUrl": {
                    "deb": "https://qqdl.gtimg.cn/QQ_3.2.29_260528_arm64_01.deb"
                },
                "loongarchDownloadUrl": {
                    "deb": "https://qqdl.gtimg.cn/QQ_3.2.29_260528_loongarch64_01.deb"
                },
            }
        }
    )
