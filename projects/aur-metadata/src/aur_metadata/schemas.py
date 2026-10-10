"""通用响应模型"""

from pydantic import BaseModel


class PackageList(BaseModel):
    """已注册包名列表"""

    packages: list[str]


class PackageInfo(BaseModel):
    """包信息：版本号 + 各架构下载 URL（原始 / 实时可下载）+ 文件 hash

    - ``urls``：原始下载 URL，写入 PKGBUILD ``source_<arch>=()`` 的稳定链接，
      永久有效、不携带任何鉴权参数；
    - ``download_urls``：查询时实时生成的**可直接下载** URL（如 QQ 经 GetSign
      换取的临时签名链接，会过期）。值为 ``None`` 表示该架构签名失败；
      整个字段为空 dict 表示本响应未提供实时链接（如 refresh 路径），
      此时消费方应回退 ``urls`` 或自行完成鉴权。
    """

    name: str
    version: str
    urls: dict[str, str]
    download_urls: dict[str, str | None] = {}
    hashes: dict[str, str | None]
