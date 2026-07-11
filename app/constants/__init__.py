"""常量与枚举定义"""

from app.constants.http import (
    CHUNK_SIZE,
    DEFAULT_TIMEOUT,
    MAX_CONCURRENT_DOWNLOADS,
    USER_AGENT,
)
from app.constants.package import ArchEnum, HashAlgorithmEnum

__all__ = [
    "ArchEnum",
    "CHUNK_SIZE",
    "DEFAULT_TIMEOUT",
    "HashAlgorithmEnum",
    "MAX_CONCURRENT_DOWNLOADS",
    "USER_AGENT",
]
