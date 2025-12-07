from enum import Enum

DOWNLOAD_DIR = "downloads"


class ArchEnum(Enum):
    X86_64 = "x86_64"
    AARCH64 = "aarch64"
    LOONG64 = "loong64"
    MIPS64EL = "mips64el"


class PackageEnum(Enum):
    QQ = "qq"


class HashAlgorithmEnum(Enum):
    """哈希算法枚举"""

    SHA256 = "sha256"
    SHA512 = "sha512"

    @classmethod
    def get_all(cls):
        """获取所有支持的哈希算法"""
        return [algo.value for algo in cls]


class ParserEnum(Enum):
    """解析器枚举"""

    QQ = "QQParser"
