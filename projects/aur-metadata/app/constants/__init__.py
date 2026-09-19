"""常量与枚举定义"""

from app.constants.http import (
    CHUNK_SIZE,
    DEFAULT_TIMEOUT,
    MAX_CONCURRENT_DOWNLOADS,
    USER_AGENT,
)
from app.constants.package import ArchEnum, HashAlgorithmEnum

__all__ = [
    "CHUNK_SIZE",
    "DEFAULT_TIMEOUT",
    "MAX_CONCURRENT_DOWNLOADS",
    "USER_AGENT",
    "ArchEnum",
    "HashAlgorithmEnum",
]
