"""配置加载器单元测试"""

from pathlib import Path

import pytest

from aur_auto_update.constants.constants import ArchEnum
from aur_auto_update.loaders.config_loader import ConfigLoader, PackageConfig


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
    """基于 tmp_path 合成配置的自包含测试，不依赖仓库真实 config.yaml"""

    @staticmethod
    def _write_config(tmp_path: Path, content: str) -> Path:
        config_file = tmp_path / "config.yaml"
        config_file.write_text(content, encoding="utf-8")
        return config_file

    def test_load_from_yaml(self, tmp_path: Path) -> None:
        self._write_config(
            tmp_path,
            """
settings:
  api:
    base_url: https://example.com/api/v1/packages
packages:
  test-pkg:
    name: test
    pkgbuild: packages/test/PKGBUILD
""",
        )
        loader = ConfigLoader.load_from_yaml(tmp_path / "config.yaml")
        assert "test-pkg" in loader.packages
        assert loader.packages["test-pkg"].name == "test"

    def test_base_dir_is_config_parent(self, tmp_path: Path) -> None:
        """base_dir 为配置文件所在目录，配置内相对路径以此为基准"""
        nested = tmp_path / "conf"
        nested.mkdir()
        self._write_config(
            nested,
            """
settings:
  api:
    base_url: https://example.com/api/v1/packages
""",
        )
        loader = ConfigLoader.load_from_yaml(nested / "config.yaml")
        assert loader.base_dir == nested

    def test_api_base_url_loaded(self, tmp_path: Path) -> None:
        """全局 api.base_url 正确加载"""
        self._write_config(
            tmp_path,
            """
settings:
  api:
    base_url: https://example.com/api/v1/packages
""",
        )
        loader = ConfigLoader.load_from_yaml(tmp_path / "config.yaml")
        assert loader.settings.api.base_url == "https://example.com/api/v1/packages"

    def test_settings_hash_algorithm_default(self, tmp_path: Path) -> None:
        """全局默认 hash_algorithm 为 b2"""
        self._write_config(
            tmp_path,
            """
settings:
  api:
    base_url: https://example.com/api/v1/packages
""",
        )
        loader = ConfigLoader.load_from_yaml(tmp_path / "config.yaml")
        assert loader.settings.hash_algorithm == "b2"

    def test_ignore_ssl_errors_default(self, tmp_path: Path) -> None:
        """全局默认不忽略 SSL 错误（证书校验开启）"""
        self._write_config(
            tmp_path,
            """
settings:
  api:
    base_url: https://example.com/api/v1/packages
""",
        )
        loader = ConfigLoader.load_from_yaml(tmp_path / "config.yaml")
        assert loader.settings.ignore_ssl_errors is False

    def test_unknown_fields_ignored(self, tmp_path: Path) -> None:
        """settings 内的未知字段被忽略"""
        self._write_config(
            tmp_path,
            """
settings:
  api:
    base_url: https://example.com/api/v1/packages
  legacy_field: ignored
""",
        )
        loader = ConfigLoader.load_from_yaml(tmp_path / "config.yaml")
        assert loader.settings.api.base_url == "https://example.com/api/v1/packages"

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
