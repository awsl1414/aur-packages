"""FastAPI 依赖：共享服务（如 PackageService）的请求级访问入口"""

from fastapi import Request

from app.response import BizError, ErrorCode
from app.services.package_service import PackageService


def get_package_service(request: Request) -> PackageService:
    """从 app.state 获取 PackageService（由 lifespan 注入）。

    作为 FastAPI 依赖，在端点参数中通过 ``Depends(get_package_service)`` 注入。
    服务未初始化时抛 BizError → 500。
    """
    service: PackageService | None = getattr(request.app.state, "package_service", None)
    if service is None:
        raise BizError(ErrorCode.INTERNAL_ERROR, "服务未初始化")
    return service
