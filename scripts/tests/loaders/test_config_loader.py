"""配置加载器单元测试"""

from pathlib import Path

import pytest

from constants.constants import ArchEnum
from loaders.config_loader import ConfigLoader, PackageConfig


class TestPackageConfig:
    def test_defaults(self) -> None:
        config = PackageConfig(
            name="test",
            pkgbuild="packages/test/PKGBUILD",
        )
        assert config.update_source_url is True
        assert config.enable is True
        assert config.arch == []
        assert config.hash_algorithm is None

    def test_get_supported_archs(self) -> None:
        config = PackageConfig(
            name="test",
            pkgbuild="packages/test/PKGBUILD",
            arch=["x86_64", "aarch64"],
        )
        archs = config.get_supported_archs()
        assert archs == [ArchEnum.X86_64, ArchEnum.AARCH64]

    def test_get_supported_archs_empty(self) -> None:
        config = PackageConfig(
            name="test",
            pkgbuild="packages/test/PKGBUILD",
        )
        assert config.get_supported_archs() == []

    def test_extra_fields_ignored(self) -> None:
        """model_config extra=ignore：传入额外字段字典时被忽略"""
        config = PackageConfig.model_validate(
            {
                "name": "test",
                "pkgbuild": "packages/test/PKGBUILD",
                "source": "ignored",
                "parser": "ignored",
            }
        )
        assert config.name == "test"

    def test_get_effective_hash_algorithm_default(self) -> None:
        """hash_algorithm 为 None 时使用全局默认"""
        config = PackageConfig(
            name="test",
            pkgbuild="packages/test/PKGBUILD",
        )
        assert config.get_effective_hash_algorithm("sha512") == "sha512"

    def test_get_effective_hash_algorithm_override(self) -> None:
        """hash_algorithm 显式设置时覆盖全局默认"""
        config = PackageConfig(
            name="test",
            pkgbuild="packages/test/PKGBUILD",
            hash_algorithm="b2",
        )
        assert config.get_effective_hash_algorithm("sha512") == "b2"


class TestConfigLoader:
    def test_load_from_yaml(self) -> None:
        loader = ConfigLoader.load_from_yaml()
        assert "linuxqq-nt" in loader.packages
        assert "navicat" in loader.packages
        assert "trae" in loader.packages
        # name 现在是 helper 包名
        assert loader.packages["linuxqq-nt"].name == "qq"
        assert loader.packages["navicat"].name == "navicat"

    def test_api_base_url_loaded(self) -> None:
        """全局 api.base_url 正确加载"""
        loader = ConfigLoader.load_from_yaml()
        assert loader.settings.api.base_url.startswith("https://")

    def test_navicat_update_source_url_disabled(self) -> None:
        """navicat URL 静态写死在 PKGBUILD，update_source_url 为 False"""
        loader = ConfigLoader.load_from_yaml()
        assert loader.packages["navicat"].update_source_url is False

    def test_settings_hash_algorithm_default(self) -> None:
        """全局默认 hash_algorithm 为 b2"""
        loader = ConfigLoader.load_from_yaml()
        assert loader.settings.hash_algorithm == "b2"

    def test_ignore_ssl_errors_default(self) -> None:
        """全局默认不忽略 SSL 错误（证书校验开启）"""
        loader = ConfigLoader.load_from_yaml()
        assert loader.settings.ignore_ssl_errors is False

    def test_zen_browser_uses_global_default(self) -> None:
        """zen-browser 使用全局默认 b2（无需包级覆盖）"""
        loader = ConfigLoader.load_from_yaml()
        zen = loader.packages["zen-browser"]
        assert zen.hash_algorithm is None
        assert zen.get_effective_hash_algorithm("b2") == "b2"

    def test_qq_default_hash_algorithm(self) -> None:
        """linuxqq-nt 包未设置 hash_algorithm，使用全局默认"""
        loader = ConfigLoader.load_from_yaml()
        qq = loader.packages["linuxqq-nt"]
        assert qq.hash_algorithm is None
        assert qq.get_effective_hash_algorithm("b2") == "b2"

    def test_load_empty_yaml(self, tmp_path: Path) -> None:
        """空 YAML 文件抛出 ValueError"""
        empty_file = tmp_path / "empty.yaml"
        empty_file.write_text("", encoding="utf-8")
        with pytest.raises(ValueError, match="配置文件为空"):
            ConfigLoader.load_from_yaml(str(empty_file))

    def test_load_missing_file(self) -> None:
        """不存在的文件抛出 FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load_from_yaml("/nonexistent/config.yaml")


class TestPackageConfigUnknownArch:
    def test_unknown_arch_skipped(self) -> None:
        """未知架构字符串被跳过"""
        config = PackageConfig(
            name="test",
            pkgbuild="packages/test/PKGBUILD",
            arch=["x86_64", "riscv64"],
        )
        archs = config.get_supported_archs()
        assert archs == [ArchEnum.X86_64]
