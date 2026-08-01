"""app.response 单元测试：成功响应构造与全局异常处理器接线。"""

from __future__ import annotations

from fastapi import FastAPI
from starlette.testclient import TestClient

from app.response import (
    _HTTP_STATUS,
    ApiResponse,
    BizError,
    ErrorCode,
    _envelope,
    register_exception_handlers,
    success,
)
from app.schemas import PackageList


def test_success_envelope() -> None:
    """success() 产出 code=0 且携带 data"""
    resp = success(PackageList(packages=["qq"]))
    assert resp.code == ErrorCode.SUCCESS
    assert resp.message == "ok"
    assert resp.data is not None and resp.data.packages == ["qq"]


def test_biz_error_carries_code_and_message() -> None:
    err = BizError(ErrorCode.PACKAGE_NOT_FOUND, "missing")
    assert err.code == 40400
    assert err.message == "missing"


def test_envelope_shape() -> None:
    assert _envelope(40400, "x") == {"code": 40400, "message": "x", "data": None}


def test_error_code_to_http_status_mapping() -> None:
    """每个业务码映射到期望 HTTP 状态码"""
    assert _HTTP_STATUS[ErrorCode.SUCCESS].value == 200
    assert _HTTP_STATUS[ErrorCode.PACKAGE_NOT_FOUND].value == 404
    assert _HTTP_STATUS[ErrorCode.VALIDATION_ERROR].value == 422
    assert _HTTP_STATUS[ErrorCode.TOO_MANY_REQUESTS].value == 429
    assert _HTTP_STATUS[ErrorCode.UPSTREAM_ERROR].value == 502
    assert _HTTP_STATUS[ErrorCode.INTERNAL_ERROR].value == 500


def _client_with(routes: dict[str, dict[str, int | str]]) -> TestClient:
    """构造带全局处理器的临时 app，按 {path: {code, message}} 注册抛 BizError 的路由"""
    app = FastAPI()
    register_exception_handlers(app)

    for path, spec in routes.items():

        def endpoint(spec: dict[str, int | str] = spec) -> None:
            raise BizError(int(spec["code"]), str(spec["message"]))

        app.add_api_route(path, endpoint, methods=["GET"])
    return TestClient(app)


def test_handler_maps_each_biz_error_status() -> None:
    """BizError → 对应 HTTP 状态码 + 统一信封"""
    client = _client_with(
        {
            "/e404": {"code": ErrorCode.PACKAGE_NOT_FOUND, "message": "m1"},
            "/e429": {"code": ErrorCode.TOO_MANY_REQUESTS, "message": "m2"},
            "/e502": {"code": ErrorCode.UPSTREAM_ERROR, "message": "m3"},
        }
    )
    cases = {"/e404": 404, "/e429": 429, "/e502": 502}
    for path, status in cases.items():
        r = client.get(path)
        assert r.status_code == status
        body = r.json()
        assert body["data"] is None
        assert body["message"]


def test_unknown_biz_error_falls_back_to_500() -> None:
    """未知业务码回退到 500"""
    client = _client_with({"/e": {"code": 99999, "message": "???"}})
    assert client.get("/e").status_code == 500


def test_unhandled_exception_returns_500() -> None:
    """未捕获异常被兜底为内部错误，不泄漏堆栈"""
    app = FastAPI()
    register_exception_handlers(app)

    def boom() -> None:
        raise RuntimeError("boom")

    app.add_api_route("/boom", boom, methods=["GET"])
    # raise_server_exceptions=False：让 Exception 处理器返回 500 而非被 TestClient 重抛
    r = TestClient(app, raise_server_exceptions=False).get("/boom")
    assert r.status_code == 500
    assert r.json() == {
        "code": ErrorCode.INTERNAL_ERROR,
        "message": "内部错误",
        "data": None,
    }


def test_api_response_generic_roundtrip() -> None:
    """ApiResponse 泛型序列化结构正确"""
    m = ApiResponse[PackageList](code=0, message="ok", data=PackageList(packages=["a"]))
    dumped = m.model_dump()
    assert dumped["data"]["packages"] == ["a"]
