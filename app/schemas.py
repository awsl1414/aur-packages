"""通用响应模型"""

from pydantic import BaseModel


class PackageList(BaseModel):
    """已注册包名列表"""

    packages: list[str]


class PackageInfo(BaseModel):
    """包信息：版本号 + 各架构原始下载 URL，可选文件 hash"""

    name: str
    version: str
    urls: dict[str, str]
    hashes: dict[str, str | None] | None = None
