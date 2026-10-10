"""常量与枚举定义。

运行参数（API 地址、下载设置等）不在此处，由 ``config.yaml`` 加载后经
构造函数注入；本包只保留不依赖环境的真正常量。
"""

from aur_auto_update.constants.package import ArchEnum, HashAlgorithmEnum

__all__ = [
    "ArchEnum",
    "HashAlgorithmEnum",
]
