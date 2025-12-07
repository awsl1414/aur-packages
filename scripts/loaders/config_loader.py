from pydantic import BaseModel, Field
from typing import List
import yaml
from constants import ArchEnum


class PackageConfig(BaseModel):
    name: str = Field(..., description="name")
    source: str
    fetch_url: str
    upstream: str
    parser: str
    pkgbuild: str
    arch: List[str] = Field(default_factory=list, description="支持的架构列表")

    class Config:
        # 允许通过 . 访问属性
        extra = "ignore"
        validate_by_name = True

    def get_supported_archs(self) -> List[ArchEnum]:
        """获取支持的架构枚举列表"""
        supported_archs = []
        for arch_str in self.arch:
            for arch_enum in ArchEnum:
                if arch_enum.value == arch_str:
                    supported_archs.append(arch_enum)
                    break
        return supported_archs


class ConfigLoader(BaseModel):
    packages: dict[str, PackageConfig]

    class Config:
        extra = "ignore"

    @classmethod
    def load_from_yaml(cls, filepath: str = "packages.yaml") -> "ConfigLoader":
        """从 YAML 文件加载"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data)
