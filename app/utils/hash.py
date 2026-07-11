"""哈希计算工具"""

import hashlib
from collections.abc import Callable
from pathlib import Path
from typing import Protocol, runtime_checkable

from app.constants import CHUNK_SIZE, HashAlgorithmEnum


@runtime_checkable
class _Hash(Protocol):
    def update(self, data: bytes, /) -> None: ...
    def hexdigest(self) -> str: ...


_HASH_BUILDERS: dict[str, Callable[[], _Hash]] = {
    HashAlgorithmEnum.SHA256.value: hashlib.sha256,
    HashAlgorithmEnum.SHA512.value: hashlib.sha512,
    HashAlgorithmEnum.B2.value: hashlib.blake2b,
}


def get_hash_builder(algorithm: str) -> Callable[[], _Hash]:
    """返回指定算法的 hash 构造器。

    供流式下载边下边算场景复用；不支持算法时抛 ValueError。
    """
    key: str = algorithm.lower()
    if key not in _HASH_BUILDERS:
        raise ValueError(
            f"不支持的哈希算法: {algorithm}，支持的算法: {list(_HASH_BUILDERS.keys())}"
        )
    return _HASH_BUILDERS[key]


def calculate_file_hash(
    file_path: str | Path,
    hash_algorithm: str = HashAlgorithmEnum.B2.value,
) -> str:
    """计算文件哈希值。

    支持：
        - blake2b (b2)
        - sha512
        - sha256

    采用分块读取方式，适用于大文件。

    Raises:
        FileNotFoundError: 文件不存在。
        IsADirectoryError: 指定路径不是普通文件。
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    if not file_path.is_file():
        raise IsADirectoryError(f"不是普通文件: {file_path}")

    hash_func = get_hash_builder(hash_algorithm)()

    with file_path.open("rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            hash_func.update(chunk)

    return hash_func.hexdigest()
