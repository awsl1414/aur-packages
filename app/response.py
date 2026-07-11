"""统一响应与错误结构"""

import logging
from http import HTTPStatus
from typing import Generic, TypeVar

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ErrorCode:
    """业务错误码：前三位对齐 HTTP 状态码，后两位为子码"""

    SUCCESS = 0
    PACKAGE_NOT_FOUND = 40400
    VALIDATION_ERROR = 42200
    UPSTREAM_ERROR = 50200
    INTERNAL_ERROR = 50000


# 业务码 → HTTP 状态码
_HTTP_STATUS: dict[int, HTTPStatus] = {
    ErrorCode.SUCCESS: HTTPStatus.OK,
    ErrorCode.PACKAGE_NOT_FOUND: HTTPStatus.NOT_FOUND,
    ErrorCode.VALIDATION_ERROR: HTTPStatus.UNPROCESSABLE_ENTITY,
    ErrorCode.UPSTREAM_ERROR: HTTPStatus.BAD_GATEWAY,
    ErrorCode.INTERNAL_ERROR: HTTPStatus.INTERNAL_SERVER_ERROR,
}


class ApiResponse(BaseModel, Generic[T]):
    """统一响应包装：code + message + data"""

    code: int
    message: str
    data: T | None = None


class BizError(Exception):
    """业务异常，携带错误码与消息，由全局处理器转为统一错误响应"""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def success(data: T) -> ApiResponse[T]:
    """构造成功响应"""
    return ApiResponse(code=ErrorCode.SUCCESS, message="ok", data=data)


def _envelope(code: int, message: str) -> dict[str, object]:
    return {"code": code, "message": message, "data": None}


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器，统一错误响应结构"""

    @app.exception_handler(BizError)
    async def _handle_biz_error(_request: Request, exc: BizError) -> JSONResponse:
        return JSONResponse(
            status_code=_HTTP_STATUS.get(exc.code, HTTPStatus.INTERNAL_SERVER_ERROR),
            content=_envelope(exc.code, exc.message),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details: str = "; ".join(
            f"{'.'.join(str(x) for x in e.get('loc', []))}: {e.get('msg', '')}"
            for e in exc.errors()
        )
        message: str = f"参数校验失败: {details}" if details else "参数校验失败"
        return JSONResponse(
            status_code=_HTTP_STATUS[ErrorCode.VALIDATION_ERROR],
            content=_envelope(ErrorCode.VALIDATION_ERROR, message),
        )

    @app.exception_handler(Exception)
    async def _handle_unhandled(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("未处理的异常: %s", exc)
        return JSONResponse(
            status_code=_HTTP_STATUS[ErrorCode.INTERNAL_ERROR],
            content=_envelope(ErrorCode.INTERNAL_ERROR, "内部错误"),
        )
