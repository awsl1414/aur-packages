"""hash 工具模块单元测试"""

from pathlib import Path

import pytest

from constants.constants import HashAlgorithmEnum
from utils.hash import calculate_file_hash


class TestCalculateFileHash:
    """calculate_file_hash 测试"""

    def test_sha512(self, tmp_path: Path) -> None:
        """正常计算 SHA512"""
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello world")
        result = calculate_file_hash(f, HashAlgorithmEnum.SHA512.value)
        assert isinstance(result, str)
        assert len(result) == 128  # SHA512 hex 长度

    def test_sha256(self, tmp_path: Path) -> None:
        """正常计算 SHA256"""
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello world")
        result = calculate_file_hash(f, HashAlgorithmEnum.SHA256.value)
        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hex 长度

    def test_b2(self, tmp_path: Path) -> None:
        """正常计算 BLAKE2b (b2)"""
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello world")
        result = calculate_file_hash(f, HashAlgorithmEnum.B2.value)
        assert isinstance(result, str)
        assert len(result) == 128  # BLAKE2b 默认 512-bit，hex 长度 128

    def test_file_not_found(self) -> None:
        """文件不存在抛出 FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            calculate_file_hash("/nonexistent/file.bin")

    def test_unsupported_algorithm(self, tmp_path: Path) -> None:
        """不支持的算法抛出 ValueError"""
        f = tmp_path / "test.bin"
        f.write_bytes(b"data")
        with pytest.raises(ValueError, match="不支持的哈希算法"):
            calculate_file_hash(f, "md5")

    def test_empty_file(self, tmp_path: Path) -> None:
        """空文件正常计算哈希"""
        f = tmp_path / "empty.bin"
        f.write_bytes(b"")
        result = calculate_file_hash(f, HashAlgorithmEnum.SHA512.value)
        assert isinstance(result, str)
        assert len(result) == 128
