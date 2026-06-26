"""哈希计算工具模块"""

import hashlib
from collections.abc import Callable
from pathlib import Path
from typing import Protocol, runtime_checkable

from constants.constants import HashAlgorithmEnum


@runtime_checkable
class _Hash(Protocol):
    def update(self, data: bytes, /) -> None: ...
    def hexdigest(self) -> str: ...


_HASH_BUILDERS: dict[str, Callable[[], _Hash]] = {
    HashAlgorithmEnum.SHA256.value: hashlib.sha256,
    HashAlgorithmEnum.SHA512.value: hashlib.sha512,
    HashAlgorithmEnum.B2.value: hashlib.blake2b,
}


def calculate_file_hash(
    file_path: str | Path, hash_algorithm: str = HashAlgorithmEnum.B2.value
) -> str:
    """
    计算文件哈希值

    支持 BLAKE2b(b2)、SHA512、SHA256 算法，分块读取大文件避免内存占用过高
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    if hash_algorithm.lower() not in _HASH_BUILDERS:
        raise ValueError(
            f"不支持的哈希算法: {hash_algorithm}，支持的算法: {list(_HASH_BUILDERS.keys())}"
        )

    hash_func = _HASH_BUILDERS[hash_algorithm.lower()]()

    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)

    return hash_func.hexdigest()
