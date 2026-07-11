"""通用包查询路由"""

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_package_service
from app.constants import HashAlgorithmEnum
from app.response import ApiResponse, BizError, ErrorCode, success
from app.schemas import PackageInfo, PackageList
from app.services.package_service import PackageNotFoundError, PackageService

router = APIRouter(prefix="/packages", tags=["packages"])


@router.get("", response_model=ApiResponse[PackageList], summary="列出所有已注册包")
async def list_packages(
    service: PackageService = Depends(get_package_service),
) -> ApiResponse[PackageList]:
    names: list[str] = await service.list_packages()
    return success(PackageList(packages=names))


@router.get(
    "/{name}",
    response_model=ApiResponse[PackageInfo],
    summary="查询指定包的最新版本与可选信息",
)
async def get_package(
    name: str,
    service: PackageService = Depends(get_package_service),
    with_hash: bool = Query(
        default=False, description="是否计算文件 hash（较慢，会下载文件）"
    ),
    algorithm: str = Query(
        default=HashAlgorithmEnum.B2.value,
        description="hash 算法：b2 / sha256 / sha512",
    ),
) -> ApiResponse[PackageInfo]:
    try:
        info: PackageInfo = await service.get_info(
            name, with_hash=with_hash, hash_algorithm=algorithm
        )
    except PackageNotFoundError:
        raise BizError(ErrorCode.PACKAGE_NOT_FOUND, f"包 '{name}' 未注册") from None
    except RuntimeError as e:
        raise BizError(ErrorCode.UPSTREAM_ERROR, str(e)) from e
    return success(info)
