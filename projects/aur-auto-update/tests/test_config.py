"""配置加载器单元测试"""

from pathlib import Path

import pytest

from aur_auto_update.config import ConfigLoader, PackageConfig
from aur_auto_update.constants import ArchEnum


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


class TestHashAlgorithmValidation:
    """hash_algorithm 配置加载期校验（配错算法会让 sums 字段静默 no-op）"""

    def test_global_invalid_algorithm_rejected(self, tmp_path: Path) -> None:
        """全局 hash_algorithm 非法时加载即报错"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
settings:
  hash_algorithm: md5
  api:
    base_url: https://example.com/api/v1/packages
""",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="未知 hash 算法"):
            ConfigLoader.load_from_yaml(config_file)

    def test_package_invalid_algorithm_rejected(self) -> None:
        """包级 hash_algorithm 非法时构造即报错"""
        with pytest.raises(ValueError, match="未知 hash 算法"):
            PackageConfig(
                name="test",
                pkgbuild="packages/test/PKGBUILD",
                hash_algorithm="md5",
            )


class TestGithubSourceConfig:
    """GitHub 回退配置：解析、规则 fail-fast 与旧配置兼容"""

    def test_github_optional(self) -> None:
        """未配置 github 的包照常加载（旧 config.yaml 兼容）"""
        config = PackageConfig(name="qq", pkgbuild="packages/qq/PKGBUILD")
        assert config.github is None

    def test_single_version_rule_wrapped(self) -> None:
        """单条版本规则写成表时自动包装成列表"""
        config = PackageConfig.model_validate(
            {
                "name": "app",
                "pkgbuild": "packages/app/PKGBUILD",
                "github": {
                    "repo": "owner/repo",
                    "version": {"source": "tag_name", "regex": r"^v(.+)$", "group": 1},
                    "assets": {"x86_64": "*_amd64.deb"},
                },
            }
        )
        assert config.github is not None
        assert len(config.github.version) == 1
        assert config.github.version[0].group == 1

    def test_repo_must_be_owner_slash_name(self) -> None:
        with pytest.raises(ValueError, match="owner/repo"):
            PackageConfig.model_validate(
                {
                    "name": "app",
                    "pkgbuild": "packages/app/PKGBUILD",
                    "github": {
                        "repo": "invalid",
                        "version": {"regex": r"v(.+)"},
                        "assets": {"x86_64": "*"},
                    },
                }
            )

    def test_group_out_of_range_rejected(self) -> None:
        """group 越界在加载期拦下，避免运行时取到空版本"""
        with pytest.raises(ValueError, match="捕获组数"):
            PackageConfig.model_validate(
                {
                    "name": "app",
                    "pkgbuild": "packages/app/PKGBUILD",
                    "github": {
                        "repo": "owner/repo",
                        "version": {"regex": r"^v(\d+)$", "group": 3},
                        "assets": {"x86_64": "*"},
                    },
                }
            )

    def test_template_and_group_conflict(self) -> None:
        with pytest.raises(ValueError, match="不可同填"):
            PackageConfig.model_validate(
                {
                    "name": "app",
                    "pkgbuild": "packages/app/PKGBUILD",
                    "github": {
                        "repo": "owner/repo",
                        "version": {
                            "regex": r"(\d+)\.(\d+)",
                            "group": 1,
                            "template": "{0}.{1}",
                        },
                        "assets": {"x86_64": "*"},
                    },
                }
            )

    def test_template_group_count_mismatch(self) -> None:
        with pytest.raises(ValueError, match="不匹配"):
            PackageConfig.model_validate(
                {
                    "name": "app",
                    "pkgbuild": "packages/app/PKGBUILD",
                    "github": {
                        "repo": "owner/repo",
                        "version": {"regex": r"(\d+)", "template": "{0}.{1}"},
                        "assets": {"x86_64": "*"},
                    },
                }
            )

    def test_invalid_source_rejected(self) -> None:
        with pytest.raises(ValueError, match="tag_name 或 name"):
            PackageConfig.model_validate(
                {
                    "name": "app",
                    "pkgbuild": "packages/app/PKGBUILD",
                    "github": {
                        "repo": "owner/repo",
                        "version": {"source": "body", "regex": r"v(.+)"},
                        "assets": {"x86_64": "*"},
                    },
                }
            )

    def test_github_assets_must_cover_archs(self) -> None:
        """github.assets 缺 arch 中的架构 → 加载期报错，而不是等 metadata 宕机才失败"""
        with pytest.raises(ValueError, match="github.assets 缺少架构"):
            PackageConfig.model_validate(
                {
                    "name": "app",
                    "pkgbuild": "packages/app/PKGBUILD",
                    "arch": ["x86_64", "aarch64"],
                    "github": {
                        "repo": "owner/repo",
                        "version": {"regex": r"v(.+)"},
                        "assets": {"x86_64": "*_amd64.deb"},
                    },
                }
            )

    def test_github_assets_covering_archs_ok(self) -> None:
        config = PackageConfig.model_validate(
            {
                "name": "app",
                "pkgbuild": "packages/app/PKGBUILD",
                "arch": ["x86_64"],
                "github": {
                    "repo": "owner/repo",
                    "version": {"regex": r"v(.+)"},
                    "assets": {"x86_64": "*_amd64.deb"},
                },
            }
        )
        assert config.github is not None
