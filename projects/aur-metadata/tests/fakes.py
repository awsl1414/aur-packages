"""测试用桩：可控解析器、Fetcher 与 registry 构造，避免真实网络。

放普通模块而非 conftest，便于测试用绝对导入（``from tests.fakes import ...``）复用。
"""

from __future__ import annotations

import asyncio
import gzip
import io
import lzma
import tarfile
from typing import cast

import zstandard

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

    def parse_version(self, response_data: str) -> str | None:
        return self._version

    def parse_url(self, arch: ArchEnum | str, response_data: str) -> str | None:
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
        head: bytes | dict[str, bytes] | None = None,
    ) -> None:
        self._text = text
        self._hashes = hashes or {}
        self._delay = delay
        self._entered = entered
        # fetch_head 预设：bytes 对所有 URL 一视同仁；dict 按 URL 精确匹配；
        # None 模拟头部下载失败
        self._head = head
        self.text_calls: int = 0
        self.hash_calls: int = 0
        self.head_calls: int = 0

    async def fetch_text(
        self, url: str, headers: dict[str, str] | None = None
    ) -> str | None:
        self.text_calls += 1
        if self._entered is not None:
            self._entered.set()
        if self._delay > 0:
            await asyncio.sleep(self._delay)
        return self._text

    async def fetch_head(
        self, url: str, max_bytes: int, headers: dict[str, str] | None = None
    ) -> bytes | None:
        self.head_calls += 1
        if self._head is None:
            return None
        if isinstance(self._head, dict):
            return self._head.get(url)
        return self._head[:max_bytes]

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


def build_deb(
    version: str = "3.14.0-7681",
    compression: str = "xz",
    control_name: str = "./control",
    tar_padding: int = 0,
) -> bytes:
    """构造最小合法 deb（ar + debian-binary + control.tar.<compression>）。

    用于版本提取相关测试；``compression`` 支持 xz/gz/zst/plain，
    ``control_name`` 可改为 ``control``（无 ``./`` 前缀变体）；
    ``tar_padding`` 在 tar 末尾追加零字节（构造解压炸弹用例）。
    """
    control = (
        f"Package: test\nVersion: {version}\nArchitecture: amd64\n"
        "Maintainer: t <t@example.com>\n"
    ).encode()
    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w") as tf:
        info = tarfile.TarInfo(control_name)
        info.size = len(control)
        tf.addfile(info, io.BytesIO(control))
    tar_bytes: bytes = tar_buf.getvalue() + b"\x00" * tar_padding

    if compression == "gz":
        payload, member = gzip.compress(tar_bytes), "control.tar.gz"
    elif compression == "xz":
        payload, member = lzma.compress(tar_bytes), "control.tar.xz"
    elif compression == "zst":
        payload, member = (
            zstandard.ZstdCompressor().compress(tar_bytes),
            "control.tar.zst",
        )
    elif compression == "plain":
        payload, member = tar_bytes, "control.tar"
    else:
        raise ValueError(f"不支持的测试压缩格式: {compression}")

    out = io.BytesIO()
    out.write(b"!<arch>\n")

    def _add_member(name: str, body: bytes) -> None:
        # ar 成员头 60 字节：name[16] date[12] uid[6] gid[6] mode[8] size[10] magic[2]；
        # 名字以 / 结尾为 padding，内容按 2 字节对齐
        header = "{:<16}{:<12}{:<6}{:<6}{:<8}{:<10}".format(
            f"{name}/", "0", "0", "0", "100644", str(len(body))
        ).encode()
        out.write(header + b"\x60\n")
        out.write(body)
        if len(body) % 2:
            out.write(b"\n")

    _add_member("debian-binary", b"2.0\n")
    _add_member(member, payload)
    return out.getvalue()


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
