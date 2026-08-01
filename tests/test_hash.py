"""app.utils.hash 单元测试"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from app.utils.hash import calculate_file_hash, get_hash_builder

# 算法名 → 对应的 hashlib 参考构造器
_REFERENCE: dict[str, Callable[[], Any]] = {
    "b2": hashlib.blake2b,
    "sha256": hashlib.sha256,
    "sha512": hashlib.sha512,
}


def test_get_hash_builder_known_algorithms() -> None:
    """b2/sha256/sha512 各返回对应构造器，且计算结果与 hashlib 一致"""
    payload = b"hello"
    for algo, ref in _REFERENCE.items():
        h = get_hash_builder(algo)()
        h.update(payload)
        ref_h = ref()
        ref_h.update(payload)
        assert h.hexdigest() == ref_h.hexdigest()


def test_get_hash_builder_case_insensitive() -> None:
    """算法名大小写不敏感"""
    assert get_hash_builder("B2")().hexdigest() == hashlib.blake2b(b"").hexdigest()


def test_get_hash_builder_unsupported_raises() -> None:
    """不支持的算法抛 ValueError"""
    with pytest.raises(ValueError):
        get_hash_builder("md5")


def test_calculate_file_hash(tmp_path: Path) -> None:
    """对临时文件计算 hash 与 hashlib 直接结果一致"""
    data = b"x" * 10_000
    f = tmp_path / "bin"
    f.write_bytes(data)
    assert calculate_file_hash(f, "b2") == hashlib.blake2b(data).hexdigest()


def test_calculate_file_hash_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        calculate_file_hash(tmp_path / "nope")


def test_calculate_file_hash_directory(tmp_path: Path) -> None:
    with pytest.raises(IsADirectoryError):
        calculate_file_hash(tmp_path)
