"""哈希计算工具"""

import hashlib
from collections.abc import Callable
from typing import Protocol, runtime_checkable

from app.constants import HashAlgorithmEnum


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
