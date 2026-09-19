"""aur-metadata 服务入口：FastAPI 应用工厂与命令行入口"""

import argparse
import logging
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import uvicorn
from apscheduler import AsyncScheduler
from fastapi import FastAPI

from aur_metadata.api.v1.router import api_router as v1_router
from aur_metadata.config import AppConfig, PackageConfig, load_config, load_packages
from aur_metadata.db import close_db, init_db
from aur_metadata.fetcher import Fetcher
from aur_metadata.response import register_exception_handlers
from aur_metadata.services.package_seeder import sync_packages_from_config
from aur_metadata.services.package_service import PackageService
from aur_metadata.services.registry_loader import load_registry_from_db
from aur_metadata.services.schedule_service import ScheduleService


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """应用生命周期：初始化 DB、同步包配置、加载注册表、启停调度器

    包配置以 DB 为运行时唯一来源——启动时先执行 schema.sql 建库，
    再把 packages.toml 的包定义 upsert 进 packages 表，最后从表加载
    构建注册表。调度器（APScheduler）与 httpx client 的生命周期均在
    yield 前后管理。运行配置（``AppConfig``）与包定义由 ``create_app``
    注入 ``app.state``。
    """
    config: AppConfig = app.state.config
    packages: list[PackageConfig] = app.state.packages

    # 1. 初始化数据库（首启执行 schema.sql 建库，不含种子数据）
    await init_db(config.database.sqlite_path)
    try:
        # 2. 同步包定义：packages.toml → packages 表（幂等 upsert，每次启动执行）
        await sync_packages_from_config(packages)
        # 3. 从 DB 加载包注册表与有效包列表（调度同步复用，不重复查库）
        registry, pkgs = await load_registry_from_db(config)

        # follow_redirects：GitHub release 等 CDN 会 302 到带签名的临时下载链接，
        # 不跟随则流式下载在重定向处直接失败
        async with httpx.AsyncClient(
            timeout=config.http.default_timeout, follow_redirects=True
        ) as client:
            fetcher: Fetcher = Fetcher(client, config.http, config.github)
            package_service: PackageService = PackageService(
                fetcher,
                registry,
                min_collect_interval_seconds=config.scheduler.min_collect_interval_seconds,
                version_stale_seconds=config.database.version_stale_seconds,
            )
            app.state.package_service = package_service

            if config.scheduler.enabled:
                # scheduler 由 async with 管理生命周期（__aexit__ 自动 stop）
                async with AsyncScheduler() as scheduler:
                    schedule_service: ScheduleService = ScheduleService(
                        scheduler, package_service, config.scheduler, config
                    )
                    app.state.schedule_service = schedule_service
                    await schedule_service.start(pkgs)
                    yield
                    await schedule_service.stop()
            else:
                app.state.schedule_service = None
                yield
    finally:
        # 覆盖配置同步/加载等早期失败路径，确保连接不随异常泄漏
        await close_db()


def create_app(config: AppConfig, packages: list[PackageConfig]) -> FastAPI:
    """构造 FastAPI 应用

    Args:
        config: 应用运行配置（configs/config.toml 加载）
        packages: 包采集定义（configs/packages.toml 加载）
    """
    app: FastAPI = FastAPI(
        title="aur-metadata",
        description="为 aur-auto-update 提供应用版本、文件 hash 等元数据的服务",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.config = config
    app.state.packages = packages
    app.include_router(v1_router, prefix="/api/v1")
    register_exception_handlers(app)
    return app


def main() -> int:
    """CLI 入口：加载配置并启动 uvicorn 服务"""
    _configure_logging()

    parser = argparse.ArgumentParser(description="aur-metadata 元数据服务")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/config.toml"),
        help="配置文件路径（默认 configs/config.toml，相对当前目录）",
    )
    parser.add_argument(
        "--packages",
        type=Path,
        default=Path("configs/packages.toml"),
        help="包采集定义路径（默认 configs/packages.toml，相对当前目录）",
    )
    parser.add_argument("--host", default=None, help="覆盖配置文件的监听地址")
    parser.add_argument("--port", type=int, default=None, help="覆盖配置文件的监听端口")
    args = parser.parse_args()

    config = load_config(args.config)
    packages = load_packages(args.packages)

    uvicorn.run(
        create_app(config, packages),
        host=args.host if args.host is not None else config.server.host,
        port=args.port if args.port is not None else config.server.port,
    )
    return 0
