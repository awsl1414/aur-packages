"""aur_metadata.config 路径解析单元测试：默认搜索、环境变量与显式参数优先级"""

from __future__ import annotations

from pathlib import Path

import pytest

from aur_metadata.config import AppConfig, load_config, load_packages

# load_config 要求的各节最小合法配置
_MINIMAL_CONFIG = """
[server]
host = "127.0.0.1"
port = 8000

[http]
user_agent = "test-agent"
default_timeout = 5.0
chunk_size = 1024
max_concurrent_downloads = 1
log_body_max_length = 100
retry_max_attempts = 1
retry_backoff_seconds = 0.0

[qq]
origin = "https://im.qq.com"
cookie_url = "https://im.qq.com/index/"
sign_url = "https://im.qq.com/sign"
oidb_command = "0x9b8e"
oidb_service_type = 1

[database]
sqlite_path = "data/test.db"
version_stale_seconds = 7200

[scheduler]
enabled = false
timezone = "Asia/Shanghai"
jitter_seconds = 0
misfire_grace_seconds = 0
min_collect_interval_seconds = 0
run_on_startup = false
"""

_MINIMAL_PACKAGES = """
[[packages]]
name = "test"
parser_type = "deb"
fetch_url = "https://example.com/config.json"
archs = ["x86_64"]
interval_seconds = 3600
"""


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


@pytest.mark.usefixtures("_clean_config_env")
def test_default_from_member_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """成员目录内运行：命中首个候选 configs/config.toml"""
    _write(tmp_path / "configs/config.toml", _MINIMAL_CONFIG)
    monkeypatch.chdir(tmp_path)
    config: AppConfig = load_config()
    assert config.server.port == 8000


@pytest.mark.usefixtures("_clean_config_env")
def test_default_from_repo_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """仓库根运行：成员位置无配置时命中 projects/aur-metadata/configs/"""
    _write(tmp_path / "projects/aur-metadata/configs/config.toml", _MINIMAL_CONFIG)
    monkeypatch.chdir(tmp_path)
    config: AppConfig = load_config()
    assert config.server.port == 8000


@pytest.mark.usefixtures("_clean_config_env")
def test_default_missing_lists_candidates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """所有候选均不存在 → FileNotFoundError 列出已尝试位置"""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError, match="已尝试"):
        load_config()


def test_env_var_beats_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """环境变量优先于默认搜索路径"""
    custom = _write(tmp_path / "custom/config.toml", _MINIMAL_CONFIG)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APP_CONFIG", str(custom))
    config: AppConfig = load_config()
    assert config.database.sqlite_path == (tmp_path / "custom/data/test.db").resolve()


def test_explicit_arg_beats_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """显式参数优先于环境变量"""
    other = _write(tmp_path / "other/config.toml", _MINIMAL_CONFIG)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APP_CONFIG", str(tmp_path / "custom/config.toml"))
    config: AppConfig = load_config(other)
    assert config.database.sqlite_path == (tmp_path / "other/data/test.db").resolve()


@pytest.mark.usefixtures("_clean_config_env")
def test_load_packages_default_from_repo_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """load_packages 与 load_config 共用同一默认搜索逻辑"""
    _write(tmp_path / "projects/aur-metadata/configs/packages.toml", _MINIMAL_PACKAGES)
    monkeypatch.chdir(tmp_path)
    packages = load_packages()
    assert [p.name for p in packages] == ["test"]
