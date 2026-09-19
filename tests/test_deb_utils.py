"""app.utils.deb 单元测试：ar 解析、control.tar 解压与版本归一化。"""

from __future__ import annotations

import io
import tarfile

import pytest

from app.utils.deb import (
    _CONTROL_TAR_MAX_BYTES,
    DebParseError,
    _version_from_control_tar,
    normalize_deb_version,
    parse_deb_control_version,
)
from tests.fakes import build_deb

# ── parse_deb_control_version ────────────────────────────────────────────────


@pytest.mark.parametrize("compression", ["xz", "gz", "zst", "plain"])
def test_parse_control_version_all_compressions(compression: str) -> None:
    """四种 control.tar 编码均能提取原始 Version 字段"""
    data = build_deb(version="3.14.0-7681", compression=compression)
    assert parse_deb_control_version(data) == "3.14.0-7681"


def test_parse_control_name_without_dot_prefix() -> None:
    """control 成员名为 ``control``（无 ./ 前缀变体）同样可提取"""
    data = build_deb(control_name="control")
    assert parse_deb_control_version(data) == "3.14.0-7681"


def test_parse_accepts_trailing_bytes() -> None:
    """头部覆盖 control 段即可，其后附加任意字节（模拟 data 段/截断余量）不影响"""
    data = build_deb() + b"\x00" * 1024
    assert parse_deb_control_version(data) == "3.14.0-7681"


def test_parse_bad_magic() -> None:
    with pytest.raises(DebParseError):
        parse_deb_control_version(b"PK\x03\x04 not an ar archive at all.....")


def test_parse_truncated_header() -> None:
    """头部不足 60 字节成员头 → 视为无 control 成员"""
    with pytest.raises(DebParseError):
        parse_deb_control_version(b"!<arch>\n" + b"debian-binary/  ")


def test_parse_no_control_member() -> None:
    """归档只有 debian-binary 成员 → 无 control.tar"""
    data = build_deb()
    # 截掉 control.tar 成员：只保留 magic + debian-binary 头（60）+ 内容（4）
    with pytest.raises(DebParseError):
        parse_deb_control_version(data[: 8 + 60 + 4])


def test_parse_truncated_control_tar_body() -> None:
    """压缩流截断在 control 成员数据内 → tar 解析失败归为结构错误。

    仅截尾部（control 完整）时部分解压后仍可正确提取，不算结构错误。
    """
    data = build_deb(compression="xz")
    # magic + debian-binary 头/体 + control.tar 头 + 仅 20 字节压缩体
    with pytest.raises(DebParseError):
        parse_deb_control_version(data[: 8 + 60 + 4 + 60 + 20])


def test_parse_control_without_version_field() -> None:
    """control 文件存在但无 Version 字段 → 结构错误"""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        payload = b"Package: test\nArchitecture: amd64\n"
        info = tarfile.TarInfo("control")
        info.size = len(payload)
        tf.addfile(info, io.BytesIO(payload))
    with pytest.raises(DebParseError):
        _version_from_control_tar("control.tar.xz", buf.getvalue())


def test_parse_control_member_missing_in_tar() -> None:
    """tar 内无 control 成员 → 结构错误"""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        payload = b"Package: test\n"
        info = tarfile.TarInfo("other")
        info.size = len(payload)
        tf.addfile(info, io.BytesIO(payload))
    with pytest.raises(DebParseError):
        _version_from_control_tar("control.tar.xz", buf.getvalue())


def test_parse_decompression_bomb_rejected() -> None:
    """解压输出超过封顶 → 拒绝（46KB 压缩可膨胀至 GB 级，必须防资源耗尽）"""
    data = build_deb(tar_padding=_CONTROL_TAR_MAX_BYTES + 1024)
    with pytest.raises(DebParseError, match="解压炸弹"):
        parse_deb_control_version(data)


# ── normalize_deb_version ────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("3.14.0-7681", "3.14.0_7681"),  # 常规 upstream-revision
        ("3.14.0", "3.14.0"),  # 无 revision
        ("1:2.0-1", "2.0_1"),  # 去 epoch
        ("1:2.0", "2.0"),  # 仅 epoch
        ("1.2.3-4-5", "1.2.3-4_5"),  # upstream 内含 -：revision 取最后一个 - 之后
    ],
)
def test_normalize_deb_version(raw: str, expected: str) -> None:
    assert normalize_deb_version(raw) == expected
