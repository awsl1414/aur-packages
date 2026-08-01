"""测试用桩：可控解析器、Fetcher 与 registry 构造，避免真实网络。

放普通模块而非 conftest，便于测试用绝对导入（``from tests.fakes import ...``）复用。
"""

from __future__ import annotations

import asyncio
from typing import Any, cast

from app.constants import ArchEnum
from app.fetcher import Fetcher
from app.parsers.base import BaseParser
from app.registry import PackageEntry, PackageRegistry


class FakeParser(BaseParser):
    """可控解析器：绕开 QQ 真实网络签名，用于采集/查询编排单测。"""

    def __init__(
        self,
        version: str | None = "1.0.0",
        url_by_arch: dict[str, str] | None = None,
    ) -> None:
        self._version = version
        self._url_by_arch = url_by_arch or {}

    def parse_version(self, response_data: str | Any) -> str | None:
        return self._version

    def parse_url(self, arch: ArchEnum | str, response_data: str | Any) -> str | None:
        return self._url_by_arch.get(self._arch_value(arch))

    async def resolve_raw_url(self, arch: ArchEnum | str, raw_url: str) -> str | None:
        """默认原样返回原始 URL（不做签名），模拟非 QQ parser。"""
        return raw_url


class FakeFetcher:
    """可控 Fetcher：fetch_text 返回预设文本，fetch_and_hash_many 返回预设 hash。

    - ``text=None`` 模拟版本源抓取失败；``hashes`` 缺某 key → 该架构 hash 为 None（下载失败）
    - ``delay``/``entered`` 用于放大锁持有窗口的并发测试（替代基于 sleep 的时序假设）
    - ``text_calls``/``hash_calls`` 计数，断言是否触网

    与 ``Fetcher`` 同构（鸭子类型），注入 PackageService 时需用 ``as_fetcher()`` 转换。
    """

    def __init__(
        self,
        text: str | None = "",
        hashes: dict[str, str | None] | None = None,
        delay: float = 0.0,
        entered: asyncio.Event | None = None,
    ) -> None:
        self._text = text
        self._hashes = hashes or {}
        self._delay = delay
        self._entered = entered
        self.text_calls: int = 0
        self.hash_calls: int = 0

    async def fetch_text(
        self, url: str, headers: dict[str, str] | None = None
    ) -> str | None:
        self.text_calls += 1
        if self._entered is not None:
            self._entered.set()
        if self._delay > 0:
            await asyncio.sleep(self._delay)
        return self._text

    async def fetch_and_hash_many(
        self,
        urls: dict[str, str],
        algorithms: list[str],
        headers: dict[str, str] | None = None,
    ) -> dict[str, dict[str, str] | None]:
        """桩：某架构在 ``_hashes`` 有值视为下载成功，全部算法均返回该 digest；缺失则 None。"""
        self.hash_calls += 1
        out: dict[str, dict[str, str] | None] = {}
        for key in urls:
            digest: str | None = self._hashes.get(key)
            out[key] = ({a: digest for a in algorithms}) if digest is not None else None
        return out

    def as_fetcher(self) -> Fetcher:
        """伪装成 Fetcher 供 PackageService 使用（ty 兼容）。"""
        return cast(Fetcher, self)


def make_qq_registry(
    archs: list[ArchEnum], version: str | None = "1.0.0"
) -> PackageRegistry:
    """构造单包 'qq' 的 registry：archs 决定可解析架构，每架构 URL 自动派生。

    抽出共享构造，避免 package_service / schedule 两个测试文件各自重复构建
    PackageEntry + PackageRegistry（结构变更只需改一处）。
    """
    url_by_arch: dict[str, str] = {a.value: f"https://x/{a.value}.deb" for a in archs}
    entry = PackageEntry(
        name="qq",
        parser=FakeParser(version, url_by_arch),
        fetch_url="https://x/cfg",
        archs=archs,
    )
    reg = PackageRegistry()
    reg.replace_all([entry])
    return reg
