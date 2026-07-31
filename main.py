#!/usr/bin/env python3
"""AUR Packages Helper 服务入口"""

import logging
import sys
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import httpx
import uvicorn
from fastapi import FastAPI

from app.api.v1.router import api_router as v1_router
from app.config import config
from app.constants import DEFAULT_TIMEOUT, ArchEnum
from app.constants.qq import QQ_FETCH_URL
from app.fetcher import Fetcher
from app.parsers.qq import QQParser
from app.registry import PackageEntry, PackageRegistry
from app.response import register_exception_handlers
from app.services.package_service import PackageService


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """应用生命周期：创建/释放共享资源"""
    _configure_logging()

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        fetcher: Fetcher = Fetcher(client)

        registry: PackageRegistry = PackageRegistry()
        registry.register(
            PackageEntry(
                name="qq",
                parser=QQParser(),
                fetch_url=QQ_FETCH_URL,
                archs=[ArchEnum.X86_64, ArchEnum.AARCH64, ArchEnum.LOONG64],
            )
        )

        app.state.package_service = PackageService(fetcher, registry)
        yield


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
