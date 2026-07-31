"""AUR Packages Helper 服务入口"""

import logging
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
import uvicorn
from apscheduler import AsyncScheduler
from fastapi import FastAPI

from app.api.v1.router import api_router as v1_router
from app.config import config
from app.constants import DEFAULT_TIMEOUT
from app.db import close_db, init_db
from app.fetcher import Fetcher
from app.response import register_exception_handlers
from app.services.package_service import PackageService
from app.services.registry_loader import load_registry_from_db
from app.services.schedule_service import ScheduleService


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """应用生命周期：初始化 DB、加载注册表、构造服务、启停调度器

    包配置以 DB 为唯一来源——启动时从 packages 表加载构建注册表，
    不再硬编码。调度器（APScheduler）与 httpx client 的生命周期均在 yield 前后管理。
    """
    _configure_logging()

    # 1. 初始化数据库（首启执行 schema.sql + 种子）
    await init_db(config.database.sqlite_path)
    # 2. 从 DB 加载包注册表与 name→id 映射
    registry, name_to_id = await load_registry_from_db()

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        fetcher: Fetcher = Fetcher(client)
        package_service: PackageService = PackageService(
            fetcher, registry, config.scheduler.min_collect_interval_seconds
        )
        app.state.package_service = package_service

        if config.scheduler.enabled:
            # scheduler 由 async with 管理生命周期（__aexit__ 自动 stop）
            async with AsyncScheduler() as scheduler:
                schedule_service: ScheduleService = ScheduleService(
                    scheduler, package_service, name_to_id, config.scheduler
                )
                app.state.schedule_service = schedule_service
                await schedule_service.start()
                yield
                await schedule_service.stop()
        else:
            app.state.schedule_service = None
            yield

    await close_db()


def create_app() -> FastAPI:
    """构造 FastAPI 应用"""
    app: FastAPI = FastAPI(
        title="AUR Packages Helper",
        description="为 aur-packages 提供应用版本、文件 hash 等信息的配套服务",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(v1_router, prefix="/api/v1")
    register_exception_handlers(app)
    return app


app: FastAPI = create_app()

HOST: str = config.server.host
PORT: int = config.server.port


if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)
