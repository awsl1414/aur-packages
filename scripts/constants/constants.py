"""常量定义模块"""

from enum import Enum


class ArchEnum(Enum):
    """支持的 CPU 架构"""

    X86_64 = "x86_64"
    AARCH64 = "aarch64"
    LOONG64 = "loong64"
    MIPS64EL = "mips64el"
    ANY = "any"


class HashAlgorithmEnum(Enum):
    """哈希算法"""

    SHA256 = "sha256"
    SHA512 = "sha512"
    B2 = "b2"
