"""常量与枚举定义。

源自 config.toml 的运行参数（HTTP 共享参数、QQ 签名参数等）不在此处，
由 ``aur_metadata.config`` 加载后经构造函数注入（见 ``Fetcher`` 与
``BaseParser``）；本包只保留不依赖环境的真正常量。
"""

from aur_metadata.constants.package import ArchEnum, HashAlgorithmEnum

__all__ = [
    "ArchEnum",
    "HashAlgorithmEnum",
]
