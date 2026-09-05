"""配置文件加载模块"""

import logging

import yaml
from pydantic import BaseModel, ConfigDict, Field

from constants.constants import ArchEnum, HashAlgorithmEnum

logger = logging.getLogger(__name__)


class DownloadSettings(BaseModel):
    """下载配置（回退下载路径使用）"""

    model_config = ConfigDict(extra="ignore")

    max_retries: int = 3
    retry_wait: int = 1
    timeout: int = 60
    connections: int = 16
    show_progress: bool = True


class ApiSettings(BaseModel):
    """helper API 配置"""

    model_config = ConfigDict(extra="ignore")

    base_url: str


class Settings(BaseModel):
    """全局配置"""

    model_config = ConfigDict(extra="ignore")

    hash_algorithm: str = HashAlgorithmEnum.B2.value
    api: ApiSettings
    download: DownloadSettings = Field(default_factory=DownloadSettings)
    # 忽略 SSL 证书校验错误（自签名/过期证书的 helper API 或上游下载源），
    # 同时作用于 httpx 客户端与 aria2c 回退下载。仅建议在受控环境中开启
    ignore_ssl_errors: bool = False


class PackageConfig(BaseModel):
    """单个包的配置。

    ``name`` 为 ``aur-packages-helper`` 中注册的包名（用于拼接 API 查询 URL）。
    """

    model_config = ConfigDict(extra="ignore")

    name: str
    pkgbuild: str
    arch: list[str] = Field(default_factory=list)
    update_source_url: bool = Field(default=True)
    enable: bool = Field(default=True)
    hash_algorithm: str | None = None

    def get_supported_archs(self) -> list[ArchEnum]:
        """将字符串架构列表转换为 ArchEnum 列表"""
        supported_archs = []
        for arch_str in self.arch:
            for arch_enum in ArchEnum:
                if arch_enum.value == arch_str:
                    supported_archs.append(arch_enum)
                    break
            else:
                logger.warning("未知的架构标识: %s", arch_str)
        return supported_archs

    def get_effective_hash_algorithm(self, default: str) -> str:
        """获取生效的哈希算法（包级覆盖 > 全局默认）"""
        return self.hash_algorithm if self.hash_algorithm else default


class ConfigLoader(BaseModel):
    """配置加载器，管理全局设置和包配置"""

    model_config = ConfigDict(extra="ignore")

    settings: Settings
    packages: dict[str, PackageConfig] = Field(default_factory=dict)

    @classmethod
    def load_from_yaml(cls, filepath: str = "config.yaml") -> "ConfigLoader":
        """从 YAML 文件加载配置"""
        with open(filepath, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data is None:
            raise ValueError(f"配置文件为空: {filepath}")
        return cls(**data)
