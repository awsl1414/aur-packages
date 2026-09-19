"""通用包查询路由"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from aur_metadata.api.deps import get_package_service, get_schedule_service
from aur_metadata.constants import HashAlgorithmEnum
from aur_metadata.response import ApiResponse, BizError, ErrorCode, success
from aur_metadata.schemas import PackageInfo, PackageList
from aur_metadata.services.package_service import (
    CollectThrottledError,
    DataNotReadyError,
    PackageNotFoundError,
    PackageService,
)
from aur_metadata.services.schedule_service import ScheduleService

router = APIRouter(prefix="/packages", tags=["packages"])

# FastAPI 依赖的 Annotated 别名：避免在参数默认值处调用 Depends（ruff B008）
PackageServiceDep = Annotated[PackageService, Depends(get_package_service)]
ScheduleServiceDep = Annotated[ScheduleService, Depends(get_schedule_service)]


@router.get("", response_model=ApiResponse[PackageList], summary="列出所有已注册包")
async def list_packages(service: PackageServiceDep) -> ApiResponse[PackageList]:
    names: list[str] = await service.list_packages()
    return success(PackageList(packages=names))


@router.post(
    "/reload",
    response_model=ApiResponse[PackageList],
    summary="重新加载 packages 表配置并同步调度",
)
async def reload_packages(
    schedule_service: ScheduleServiceDep,
) -> ApiResponse[PackageList]:
    """新增/修改/删除 packages 行后调用，使 registry 与 schedule 即时对齐 DB。

    返回重载后 enabled 的包名列表。需调度器已启用（scheduler.enabled=true）。
    """
    names: list[str] = await schedule_service.reload()
    return success(PackageList(packages=names))


@router.get(
    "/{name}",
    response_model=ApiResponse[PackageInfo],
    summary="查询指定包的最新版本与文件 hash",
)
async def get_package(
    name: str,
    service: PackageServiceDep,
    algorithm: Annotated[
        str, Query(description="hash 算法：b2 / sha256 / sha512")
    ] = HashAlgorithmEnum.B2.value,
) -> ApiResponse[PackageInfo]:
    try:
        info: PackageInfo = await service.get_info(name, hash_algorithm=algorithm)
    except PackageNotFoundError:
        raise BizError(ErrorCode.PACKAGE_NOT_FOUND, f"包 '{name}' 未注册") from None
    except DataNotReadyError:
        raise BizError(
            ErrorCode.DATA_NOT_READY, f"包 '{name}' 数据尚未就绪，请稍后重试"
        ) from None
    return success(info)


@router.post(
    "/{name}/refresh",
    response_model=ApiResponse[PackageInfo],
    summary="手动触发采集并落库（复用定时采集路径）",
)
async def refresh_package(
    name: str,
    schedule_service: ScheduleServiceDep,
) -> ApiResponse[PackageInfo]:
    try:
        info: PackageInfo = await schedule_service.collect_now(name)
    except PackageNotFoundError:
        raise BizError(ErrorCode.PACKAGE_NOT_FOUND, f"包 '{name}' 未注册") from None
    except CollectThrottledError:
        raise BizError(
            ErrorCode.TOO_MANY_REQUESTS,
            f"包 '{name}' 采集过于频繁，请稍后重试",
        ) from None
    except RuntimeError as e:
        raise BizError(ErrorCode.UPSTREAM_ERROR, str(e)) from e
    return success(info)
