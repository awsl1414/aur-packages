"""aur_metadata.api.v1.packages 路由测试：异常 → 业务码映射。

直接调用路由处理函数（绕过 FastAPI 依赖注入），用 Fake 服务控制异常，验证
GET 的 PackageNotFoundError / DataNotReadyError 与 refresh 的
PackageNotFoundError / CollectThrottledError / RuntimeError 分别映射到对应业务码。
"""

from __future__ import annotations

from typing import Any, cast

import pytest

from aur_metadata.api.v1.packages import (
    get_package,
    list_packages,
    refresh_package,
    reload_packages,
)
from aur_metadata.response import BizError, ErrorCode
from aur_metadata.schemas import PackageInfo
from aur_metadata.services.package_service import (
    CollectThrottledError,
    DataNotReadyError,
    PackageNotFoundError,
    PackageService,
)
from aur_metadata.services.schedule_service import ScheduleService


class FakePackageService:
    """可控 PackageService：按预设行为驱动 get_package / list_packages"""

    def __init__(
        self,
        *,
        info: PackageInfo | None = None,
        error: Exception | None = None,
        names: list[str] | None = None,
    ) -> None:
        self._info = info
        self._error = error
        self._names = names or []

    async def list_packages(self) -> list[str]:
        return self._names

    async def get_info(self, name: str, hash_algorithm: str = "b2") -> PackageInfo:
        if self._error is not None:
            raise self._error
        assert self._info is not None
        return self._info


class FakeScheduleService:
    """可控 ScheduleService：驱动 refresh_package / reload_packages"""

    def __init__(
        self,
        *,
        info: PackageInfo | None = None,
        error: Exception | None = None,
        names: list[str] | None = None,
    ) -> None:
        self._info = info
        self._error = error
        self._names = names or []

    async def collect_now(self, name: str) -> PackageInfo:
        if self._error is not None:
            raise self._error
        assert self._info is not None
        return self._info

    async def reload(self) -> list[str]:
        return self._names


def _info() -> PackageInfo:
    return PackageInfo(
        name="qq", version="1.0.0", urls={"x86_64": "u"}, hashes={"x86_64": "h"}
    )


def _svc_pkg(**kw: Any) -> PackageService:
    return cast(PackageService, FakePackageService(**kw))


def _svc_sched(**kw: Any) -> ScheduleService:
    return cast(ScheduleService, FakeScheduleService(**kw))


# ── list / reload 成功 ──────────────────────────────────────────────────────


async def test_list_packages_ok() -> None:
    resp = await list_packages(_svc_pkg(names=["qq", "wechat"]))
    assert resp.code == 0
    assert resp.data is not None and resp.data.packages == ["qq", "wechat"]


async def test_reload_ok() -> None:
    resp = await reload_packages(_svc_sched(names=["qq"]))
    assert resp.code == 0
    assert resp.data is not None and resp.data.packages == ["qq"]


# ── get_package 异常映射 ─────────────────────────────────────────────────────


async def test_get_package_not_found() -> None:
    svc = _svc_pkg(error=PackageNotFoundError("qq"))
    with pytest.raises(BizError) as exc:
        await get_package("qq", service=svc)
    assert exc.value.code == ErrorCode.PACKAGE_NOT_FOUND


async def test_get_package_data_not_ready() -> None:
    svc = _svc_pkg(error=DataNotReadyError("qq"))
    with pytest.raises(BizError) as exc:
        await get_package("qq", service=svc)
    assert exc.value.code == ErrorCode.DATA_NOT_READY


async def test_get_package_success() -> None:
    svc = _svc_pkg(info=_info())
    resp = await get_package("qq", service=svc)
    assert resp.code == 0
    assert resp.data is not None and resp.data.version == "1.0.0"


# ── refresh_package 异常映射 ────────────────────────────────────────────────


async def test_refresh_not_found() -> None:
    svc = _svc_sched(error=PackageNotFoundError("qq"))
    with pytest.raises(BizError) as exc:
        await refresh_package("qq", schedule_service=svc)
    assert exc.value.code == ErrorCode.PACKAGE_NOT_FOUND


async def test_refresh_throttled() -> None:
    svc = _svc_sched(error=CollectThrottledError("qq"))
    with pytest.raises(BizError) as exc:
        await refresh_package("qq", schedule_service=svc)
    assert exc.value.code == ErrorCode.TOO_MANY_REQUESTS


async def test_refresh_upstream_error() -> None:
    svc = _svc_sched(error=RuntimeError("upstream down"))
    with pytest.raises(BizError) as exc:
        await refresh_package("qq", schedule_service=svc)
    assert exc.value.code == ErrorCode.UPSTREAM_ERROR


async def test_refresh_success() -> None:
    svc = _svc_sched(info=_info())
    resp = await refresh_package("qq", schedule_service=svc)
    assert resp.code == 0
    assert resp.data is not None and resp.data.version == "1.0.0"
