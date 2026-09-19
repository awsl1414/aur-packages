"""load_packages 结构校验测试"""

from pathlib import Path

import pytest

from aur_metadata.config import PackageConfig, load_packages

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 仓库自带配置：8 个包全部 interval 模式（ schema.sql 迁移的完整定义）
_DEFAULT_PACKAGE_NAMES: set[str] = {
    "qq",
    "navicat",
    "bt-dualboot-ng",
    "trae",
    "trae-sg",
    "trae-us",
    "trae-cn",
    "zen-browser",
}


def _write_config(tmp_path: Path, content: str) -> Path:
    path: Path = tmp_path / "packages.toml"
    path.write_text(content, encoding="utf-8")
    return path


def test_load_default_packages_file() -> None:
    """仓库默认 packages.toml 必须始终可加载且包集合符合预期（防配置回退）。

    逐一断言各 trae 的 region：[[packages]] 的子表按 TOML 语义绑定到最近的
    条目，条目顺序被打乱时会静默挂错包，靠这里的断言兜底。
    """
    packages: list[PackageConfig] = load_packages(_PROJECT_ROOT / "configs" / "packages.toml")
    assert {p.name for p in packages} == _DEFAULT_PACKAGE_NAMES
    assert all(p.schedule_type == "interval" for p in packages)
    navicat = next(p for p in packages if p.name == "navicat")
    assert navicat.parser_config["urls"]["x86_64"].endswith(".AppImage")
    by_name: dict[str, PackageConfig] = {p.name: p for p in packages}
    assert by_name["trae"].parser_config == {"region": "cn"}
    assert by_name["trae-sg"].parser_config == {"region": "sg"}
    assert by_name["trae-us"].parser_config == {"region": "va"}
    assert by_name["trae-cn"].parser_config == {"region": "cn"}
    assert by_name["bt-dualboot-ng"].parser_config == {}
    assert by_name["zen-browser"].parser_config == {}


def test_load_rejects_missing_packages_key(tmp_path: Path) -> None:
    """顶层键缺失（拼错/文件被清空）必须报错，而非静默降级为空包列表"""
    path: Path = _write_config(tmp_path, "package = []\n")
    with pytest.raises(ValueError, match="缺少"):
        load_packages(path)


def test_load_allows_explicit_empty_packages(tmp_path: Path) -> None:
    path: Path = _write_config(tmp_path, "packages = []\n")
    assert load_packages(path) == []


def test_load_parses_fields_with_defaults(tmp_path: Path) -> None:
    path: Path = _write_config(
        tmp_path,
        """
        [[packages]]
        name = "demo"
        parser_type = "pypi"
        fetch_url = "https://pypi.org/pypi/demo/json"
        archs = ["any"]
        interval_seconds = 60
        """,
    )
    (pkg,) = load_packages(path)
    assert pkg.parser_type == "pypi"
    assert pkg.archs == ["any"]
    assert pkg.parser_config == {}
    assert pkg.enabled is True
    assert pkg.description is None
    assert pkg.schedule_type == "interval"
    assert pkg.interval_seconds == 60
    assert pkg.cron_expr is None


def test_load_cron_schedule(tmp_path: Path) -> None:
    path: Path = _write_config(
        tmp_path,
        """
        [[packages]]
        name = "demo"
        parser_type = "zen"
        fetch_url = "https://example.com"
        archs = ["x86_64"]
        cron_expr = "30 3 * * *"
        description = "每日 3:30"
        """,
    )
    (pkg,) = load_packages(path)
    assert pkg.schedule_type == "cron"
    assert pkg.cron_expr == "30 3 * * *"
    assert pkg.description == "每日 3:30"


def test_load_rejects_schedule_missing_and_both(tmp_path: Path) -> None:
    missing: Path = _write_config(
        tmp_path,
        """
        [[packages]]
        name = "demo"
        parser_type = "zen"
        fetch_url = "https://example.com"
        archs = ["x86_64"]
        """,
    )
    with pytest.raises(ValueError, match="恰好填写一个"):
        load_packages(missing)

    both: Path = _write_config(
        tmp_path,
        """
        [[packages]]
        name = "demo"
        parser_type = "zen"
        fetch_url = "https://example.com"
        archs = ["x86_64"]
        interval_seconds = 60
        cron_expr = "30 3 * * *"
        """,
    )
    with pytest.raises(ValueError, match="恰好填写一个"):
        load_packages(both)


def test_load_rejects_duplicate_name_and_unknown_key(tmp_path: Path) -> None:
    dup: Path = _write_config(
        tmp_path,
        """
        [[packages]]
        name = "demo"
        parser_type = "zen"
        fetch_url = "https://example.com"
        archs = ["x86_64"]
        interval_seconds = 60

        [[packages]]
        name = "demo"
        parser_type = "zen"
        fetch_url = "https://example.com"
        archs = ["x86_64"]
        interval_seconds = 60
        """,
    )
    with pytest.raises(ValueError, match="name 重复"):
        load_packages(dup)

    unknown: Path = _write_config(
        tmp_path,
        """
        [[packages]]
        name = "demo"
        parser_type = "zen"
        fetch_url = "https://example.com"
        archs = ["x86_64"]
        intervel_seconds = 60
        """,
    )
    with pytest.raises(ValueError, match="未知字段"):
        load_packages(unknown)


def test_load_rejects_bad_field_types(tmp_path: Path) -> None:
    bad: Path = _write_config(
        tmp_path,
        """
        [[packages]]
        name = "demo-bad-interval"
        parser_type = "zen"
        fetch_url = "https://example.com"
        archs = ["x86_64"]
        interval_seconds = 0

        [[packages]]
        name = "demo-bad-enabled"
        parser_type = "zen"
        fetch_url = "https://example.com"
        archs = ["x86_64"]
        interval_seconds = 60
        enabled = "yes"
        """,
    )
    # 多条错误一次性报全，而非逐次试错
    with pytest.raises(ValueError) as exc_info:
        load_packages(bad)
    message: str = str(exc_info.value)
    assert "interval_seconds 必须为正整数" in message
    assert "enabled 必须为布尔值" in message
