"""create_app + lifespan 装配集成测试。

通过 TestClient 驱动完整 lifespan 生命周期，验证手动冒烟覆盖的装配路径：
真实 schema.sql 建库、包定义同步进 DB、注册表加载、服务挂载 app.state、
异常处理器注册。调度器关闭保证全程不触网（真实 Fetcher 仅构造不请求；
无快照的 GET 会 fire-and-forget 后台采集，属触网路径，不在本测试覆盖
范围，由 API 单测的 Fake 服务分层保障）。
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from aur_metadata.cli import create_app
from aur_metadata.config import AppConfig, PackageConfig
from tests.fakes import make_app_config


def _config(tmp_path: Path) -> AppConfig:
    """调度器关闭 + SQLite 落在 tmp_path 的真实 AppConfig"""
    config = make_app_config()
    return replace(
        config,
        database=replace(
            config.database, sqlite_path=tmp_path / "data" / "aur_packages.db"
        ),
        scheduler=replace(config.scheduler, enabled=False),
    )


def _package(name: str) -> PackageConfig:
    return PackageConfig(
        name=name,
        parser_type="deb",
        fetch_url="https://example.com/config.json",
        archs=["x86_64"],
        parser_config={"urls": {"amd64": "https://example.com/a.deb"}},
        enabled=True,
        interval_seconds=3600,
        cron_expr=None,
        description=None,
    )


def test_lifespan_assembles_services_and_seeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """启动：建库 → 种子同步 → 注册表加载；查询：列表与未注册包 404"""
    monkeypatch.chdir(tmp_path)
    config = _config(tmp_path)
    app = create_app(config, [_package("test-deb")])

    with TestClient(app) as client:
        # 1. 种子同步 + 注册表加载：GET /packages 纯读注册表，返回已启用包
        resp = client.get("/api/v1/packages")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["packages"] == ["test-deb"]

        # 2. 服务装配产物挂在 app.state
        assert app.state.package_service is not None
        assert app.state.schedule_service is None  # 调度器已关闭

        # 3. 未注册包 → 404 业务码（注册表未命中，不触发后台采集）
        resp = client.get("/api/v1/packages/no-such-package")
        assert resp.status_code == 404
        assert resp.json()["code"] == 40400

    # 4. 生命周期结束：DB 文件落在配置指定的绝对路径
    assert (tmp_path / "data" / "aur_packages.db").exists()
