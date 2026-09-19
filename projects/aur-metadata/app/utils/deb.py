"""deb 包版本提取工具。

从 deb 文件**头部字节**解析 control 段的 ``Version`` 字段——版本号位于第二个
ar 成员 ``control.tar.*``（deb(5) 规定成员顺序固定：debian-binary → control → data），
通常仅几十 KB，无需下载体积庞大的 data 段。

ar 归档格式：8 字节 magic ``!<arch>\n``，其后每 60 字节一个成员头
（name[16] + date[12] + uid[6] + gid[6] + mode[8] + size[10] + `\x60\\n`[2]），
成员内容按 2 字节对齐。成员名带尾部 ``/`` padding，需 rstrip。
不处理 GNU ar 长文件名扩展（``/N``、``//``）——deb(5) 固定三个短名成员，不会触达。

本模块为纯内存函数，不做任何 IO，便于单测与上层（parser/服务）自由组合。
"""

import gzip
import io
import lzma
import tarfile
from typing import IO

import zstandard

# ar 归档 magic 与成员头长度
_AR_MAGIC: bytes = b"!<arch>\n"
_AR_HEADER_SIZE: int = 60

# control 段成员名前缀（control.tar / control.tar.gz / .xz / .zst）
_CONTROL_TAR_PREFIX: str = "control.tar"

# control.tar 解压输出上限。真实 control 段（control + md5sums + 维护脚本）
# 远小于 1MB；256KB 压缩头部可声称膨胀至 GB 级，必须封顶防解压炸弹
_CONTROL_TAR_MAX_BYTES: int = 32 * 1024 * 1024

# control.tar 内 control 成员的候选名（dpkg-deb 打包为 ./control）
_CONTROL_CANDIDATES: tuple[str, ...] = ("./control", "control")


class DebParseError(Exception):
    """deb 头部结构不符合预期（magic/成员/control 缺失或损坏）"""


def parse_deb_control_version(data: bytes) -> str:
    """从 deb 文件头部字节提取 control 的原始 ``Version`` 字段值。

    只需覆盖到 control.tar 成员结束的前缀字节即可，data 截断在 control 段之后
    无影响。支持 gzip/xz/zstd/未压缩四种 control.tar 编码。

    结构不符（非 ar、成员缺失、压缩/tar 损坏、无 Version 字段）抛 ``DebParseError``。
    """
    if not data.startswith(_AR_MAGIC):
        raise DebParseError("非 ar 归档（magic 不符）")

    pos: int = len(_AR_MAGIC)
    while pos + _AR_HEADER_SIZE <= len(data):
        header: bytes = data[pos : pos + _AR_HEADER_SIZE]
        # 成员名 ASCII，尾部 / 为 padding
        name: str = header[:16].decode("ascii", errors="replace").strip().rstrip("/")
        try:
            size: int = int(header[48:58].decode("ascii").strip())
        except ValueError as e:
            raise DebParseError(f"ar 成员 {name!r} 大小字段非法") from e
        if header[58:60] != b"\x60\n":
            raise DebParseError(f"ar 成员 {name!r} 头部 magic 非法")
        body_start: int = pos + _AR_HEADER_SIZE
        # control.tar 必然先于 data 段，命中即可解析；后续成员无需再扫
        if name.startswith(_CONTROL_TAR_PREFIX):
            raw: bytes = data[body_start : body_start + size]
            return _version_from_control_tar(name, raw)
        # ar 成员内容按 2 字节对齐
        pos = body_start + size + (size % 2)
    raise DebParseError("归档头部范围内未找到 control.tar.* 成员")


def _version_from_control_tar(member_name: str, raw: bytes) -> str:
    """解压 control.tar 成员并提取 ``Version`` 字段原始值"""
    tar_bytes: bytes
    try:
        if member_name.endswith(".gz"):
            with gzip.GzipFile(fileobj=io.BytesIO(raw)) as gz:
                tar_bytes = gz.read(_CONTROL_TAR_MAX_BYTES + 1)
        elif member_name.endswith(".xz"):
            # max_length 限制单次输出，配合超限检查防解压炸弹
            tar_bytes = lzma.LZMADecompressor().decompress(
                raw, _CONTROL_TAR_MAX_BYTES + 1
            )
        elif member_name.endswith(".zst"):
            # zstd 帧可能不带内容大小，用 stream_reader 而非 decompress
            tar_bytes = (
                zstandard.ZstdDecompressor()
                .stream_reader(io.BytesIO(raw))
                .read(_CONTROL_TAR_MAX_BYTES + 1)
            )
        else:
            tar_bytes = raw
    except Exception as e:
        # 输入是不可信的二进制数据，解压库的任意异常都归为结构损坏
        raise DebParseError(f"control.tar 解压失败（{member_name}）: {e}") from e
    if len(tar_bytes) > _CONTROL_TAR_MAX_BYTES:
        raise DebParseError(
            f"control.tar 解压输出超过 {_CONTROL_TAR_MAX_BYTES} 字节（疑似解压炸弹）"
        )

    content: bytes
    try:
        with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:") as tf:
            member: tarfile.TarInfo | None = None
            for candidate in _CONTROL_CANDIDATES:
                try:
                    member = tf.getmember(candidate)
                    break
                except KeyError:
                    continue
            if member is None:
                raise DebParseError("control.tar 中无 control 成员")
            handle: IO[bytes] | None = tf.extractfile(member)
            if handle is None:
                raise DebParseError("control 成员不是普通文件")
            content = handle.read()
    except DebParseError:
        raise
    except Exception as e:
        raise DebParseError(f"control.tar 解析失败: {e}") from e

    for line in content.decode("utf-8", errors="replace").splitlines():
        if line.lower().startswith("version:"):
            return line.split(":", 1)[1].strip()
    raise DebParseError("control 文件缺少 Version 字段")


def normalize_deb_version(version: str) -> str:
    """将 deb ``Version`` 字段（``[epoch:]upstream[-revision]``）归一化为服务版本号。

    - 去 epoch（第三方应用包几乎不用，且下游 pkgver 不接受 ``:``）
    - revision 与 upstream 以 ``_`` 连接（与既有 ``<version>_<build>`` 口径一致，
      下游 pkgver 不接受 ``-``）；按 Debian policy，revision 是**最后一个** ``-``
      之后的部分，upstream 段允许内含 ``-``
    """
    if ":" in version:
        version = version.split(":", 1)[1]
    if "-" in version:
        upstream, _, revision = version.rpartition("-")
        if upstream:
            return f"{upstream}_{revision}"
    return version
