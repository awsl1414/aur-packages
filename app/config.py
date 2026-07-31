"""TOML 配置加载模块"""

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_CONFIG_ENV_VAR = "APP_CONFIG"
_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.toml"


@dataclass(frozen=True)
class ServerConfig:
    """服务监听地址与端口"""

    host: str
    port: int


@dataclass(frozen=True)
class HttpConfig:
    """HTTP 客户端相关配置"""

    user_agent: str
    default_timeout: float
    chunk_size: int
    max_concurrent_downloads: int
    log_body_max_length: int


@dataclass(frozen=True)
class QQConfig:
    """QQ 解析器相关配置"""

    fetch_url: str
    origin: str
    cookie_url: str
    sign_url: str
    oidb_command: str
    oidb_service_type: int


@dataclass(frozen=True)
class AppConfig:
    """应用根配置，聚合各子配置"""

    server: ServerConfig
    http: HttpConfig
    qq: QQConfig


def load_config(path: Path | str | None = None) -> AppConfig:
    """加载 TOML 配置文件。

    默认查找项目根 ``config.toml``，可通过环境变量
    ``APP_CONFIG`` 指定自定义路径。
    """
    config_path: Path = (
        Path(path)
        if path is not None
        else Path(os.environ.get(_CONFIG_ENV_VAR, _DEFAULT_CONFIG_PATH))
    )
    with open(config_path, "rb") as f:
        data: dict[str, dict[str, Any]] = tomllib.load(f)

    server_data: dict[str, Any] = data["server"]
    http_data: dict[str, Any] = data["http"]
    qq_data: dict[str, Any] = data["qq"]

    return AppConfig(
        server=ServerConfig(
            host=str(server_data["host"]),
            port=int(server_data["port"]),
        ),
        http=HttpConfig(
            user_agent=str(http_data["user_agent"]),
            default_timeout=float(http_data["default_timeout"]),
            chunk_size=int(http_data["chunk_size"]),
            max_concurrent_downloads=int(http_data["max_concurrent_downloads"]),
            log_body_max_length=int(http_data["log_body_max_length"]),
        ),
        qq=QQConfig(
            fetch_url=str(qq_data["fetch_url"]),
            origin=str(qq_data["origin"]),
            cookie_url=str(qq_data["cookie_url"]),
            sign_url=str(qq_data["sign_url"]),
            oidb_command=str(qq_data["oidb_command"]),
            oidb_service_type=int(qq_data["oidb_service_type"]),
        ),
    )


config: AppConfig = load_config()
