"""API v1 路由聚合器"""

from fastapi import APIRouter

from aur_metadata.api.v1.packages import router as packages_router

api_router = APIRouter()
api_router.include_router(packages_router)
