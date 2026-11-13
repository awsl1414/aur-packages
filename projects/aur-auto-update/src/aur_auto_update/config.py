"""配置文件加载模块"""

import logging
import re
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aur_auto_update.constants import ArchEnum, HashAlgorithmEnum

logger = logging.getLogger(__name__)

# 合法的 hash 算法取值（配置加载期 fail-fast：配错算法会让 sums 字段静默 no-op）
_VALID_ALGORITHMS: frozenset[str] = frozenset(a.value for a in HashAlgorithmEnum)


def _validate_hash_algorithm(value: str) -> str:
    """校验 hash 算法配置值，非法抛 ValueError"""
    if value not in _VALID_ALGORITHMS:
        raise ValueError(
            f"未知 hash 算法: {value!r}，支持的算法: {sorted(_VALID_ALGORITHMS)}"
        )
    return value


class DownloadSettings(BaseModel):
    """下载配置（下载安装包计算校验和时使用）"""

    model_config = ConfigDict(extra="ignore")

    max_retries: int = 3
    retry_wait: int = 1
    timeout: int = 60
    connections: int = 16
    show_progress: bool = True


class ApiSettings(BaseModel):
    """metadata API 配置"""

    model_config = ConfigDict(extra="ignore")

    base_url: str


class Settings(BaseModel):
    """全局配置"""

    model_config = ConfigDict(extra="ignore")

    hash_algorithm: str = HashAlgorithmEnum.B2.value
    api: ApiSettings
    download: DownloadSettings = Field(default_factory=DownloadSettings)
    # 忽略 SSL 证书校验错误（自签名/过期证书的 metadata API 或上游下载源），
    # 同时作用于 httpx 客户端与 aria2c 下载。仅建议在受控环境中开启
    ignore_ssl_errors: bool = False

    @field_validator("hash_algorithm")
    @classmethod
    def _check_hash_algorithm(cls, value: str) -> str:
        return _validate_hash_algorithm(value)


class VersionRule(BaseModel):
    """GitHub release 的版本提取规则。

    ``source`` 指定从 release JSON 的哪个字段取原始值（``tag_name`` / ``name``），
    ``regex`` 提取版本，``group`` 取捕获组或 ``template`` 拼接多个捕获组。
    多条规则按顺序 fallback（如 zen 的「带日期」与「纯版本号」两种形态）。
    """

    model_config = ConfigDict(extra="ignore")

    source: str = "tag_name"
    regex: str
    group: int = 0
    template: str | None = None

    @field_validator("source")
    @classmethod
    def _check_source(cls, value: str) -> str:
        if value not in ("tag_name", "name"):
            raise ValueError(f"version.source 必须为 tag_name 或 name，得到 {value!r}")
        return value

    @field_validator("group")
    @classmethod
    def _check_group(cls, value: int) -> int:
        if value < 0:
            raise ValueError(f"version.group 必须为非负整数，得到 {value}")
        return value

    @model_validator(mode="after")
    def _check_group_template(self) -> "VersionRule":
        if self.template is not None and self.group != 0:
            raise ValueError("version.group 与 version.template 不可同填")
        # 构造期编译并试格式化，配置错误在加载时暴露而非运行时静默空值
        compiled = re.compile(self.regex)
        if self.template is None:
            if self.group > compiled.groups:
                raise ValueError(
                    f"version.group {self.group} 超出 regex 捕获组数 {compiled.groups}"
                )
        else:
            try:
                self.template.format(*([""] * compiled.groups))
            except (IndexError, KeyError, ValueError) as e:
                raise ValueError(f"version.template 与 regex 捕获组数不匹配: {e}") from e
        return self


class GithubSourceConfig(BaseModel):
    """GitHub 来源包的回退解析配置。

    仅在 metadata API 请求失败时启用；``assets`` 为架构 → asset 匹配规则：
    以 ``*`` 开头表示后缀匹配，否则按完整文件名匹配。架构键须覆盖
    ``PackageConfig.get_supported_archs()``。
    """

    model_config = ConfigDict(extra="ignore")

    repo: str
    # GitHub release 的 tag；为空表示 /releases/latest
    tag: str | None = None
    version: list[VersionRule] = Field(min_length=1)
    assets: dict[str, str]

    @field_validator("version", mode="before")
    @classmethod
    def _wrap_single_rule(cls, value: object) -> object:
        """允许单条规则写成表、多条写成表数组"""
        if isinstance(value, dict):
            return [value]
        return value

    @field_validator("repo")
    @classmethod
    def _check_repo(cls, value: str) -> str:
        if value.count("/") != 1 or not all(value.split("/")):
            raise ValueError(f"github.repo 须为 owner/repo 形式，得到 {value!r}")
        return value


class PackageConfig(BaseModel):
    """单个包的配置。

    ``name`` 为 ``aur-metadata`` 中注册的包名（用于拼接 API 查询 URL）。
    ``github`` 可选：配置后该包在 metadata 请求失败时回退到本地 GitHub
    release 解析。
    """

    model_config = ConfigDict(extra="ignore")

    name: str
    pkgbuild: str
    arch: list[str] = Field(default_factory=list)
    update_source_url: bool = Field(default=True)
    enable: bool = Field(default=True)
    hash_algorithm: str | None = None
    github: GithubSourceConfig | None = None

    @model_validator(mode="after")
    def _check_github_assets_cover_archs(self) -> "PackageConfig":
        """github.assets 必须覆盖 arch 清单。

        回退路径缺任一架构的 asset 就只能整体放弃该包；若等到 metadata 宕机时
        才发现，等于回退在最需要它的场景失效。此处启动即失败。
        """
        if self.github is None:
            return self
        missing: list[str] = [a for a in self.arch if a not in self.github.assets]
        if missing:
            raise ValueError(
                f"包 {self.name}: github.assets 缺少架构 {missing}"
                f"（arch 为 {self.arch}）"
            )
        return self

    @field_validator("hash_algorithm")
    @classmethod
    def _check_hash_algorithm(cls, value: str | None) -> str | None:
        return value if value is None else _validate_hash_algorithm(value)

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
    """配置加载器，管理全局设置和包配置

    ``base_dir`` 为配置文件所在目录，配置内的相对路径（如 ``pkgbuild``）
    均以该目录为基准解析。
    """

    model_config = ConfigDict(extra="ignore")

    settings: Settings
    packages: dict[str, PackageConfig] = Field(default_factory=dict)
    # 不参与序列化，仅用于配置内相对路径的解析
    base_dir: Path = Field(exclude=True)

    @classmethod
    def load_from_yaml(cls, filepath: str | Path = "config.yaml") -> "ConfigLoader":
        """从 YAML 文件加载配置

        Args:
            filepath: 配置文件路径；相对路径相对当前工作目录解析

        Returns:
            加载完成的 ConfigLoader，``base_dir`` 为配置文件所在目录
        """
        path = Path(filepath)
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data is None:
            raise ValueError(f"配置文件为空: {path}")
        return cls(**data, base_dir=path.resolve().parent)
