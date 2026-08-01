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
    # 瞬时网络错误（连接超时/TLS 重置/对端中断等）的总尝试次数（含首次），1 表示不重试
    retry_max_attempts: int
    # 指数退避基数（秒）：第 n 次重试前等待 backoff * 2**(n-1)
    retry_backoff_seconds: float


@dataclass(frozen=True)
class QQConfig:
    """QQ 解析器相关配置（签名流程参数；版本源 URL 由 packages 表管理）"""

    origin: str
    cookie_url: str
    sign_url: str
    oidb_command: str
    oidb_service_type: int


@dataclass(frozen=True)
class DatabaseConfig:
    """数据库相关配置"""

    # 已解析为绝对路径的 SQLite 文件路径（相对项目根的配置会被展开）
    sqlite_path: Path
    # GET /{name} 命中 DB 快照的最大年龄（秒）；超过则回源实时下载计算
    hash_cache_ttl_seconds: int


@dataclass(frozen=True)
class GithubConfig:
    """GitHub 认证配置（应对匿名调用 api.github.com 的限流）。

    token 为空时所有请求匿名发送。优先级：环境变量 ``GITHUB_TOKEN`` > 配置文件。
    """

    token: str | None


@dataclass(frozen=True)
class SchedulerConfig:
    """定时采集调度器配置"""

    enabled: bool
    timezone: str
    jitter_seconds: int
    misfire_grace_seconds: int
    # 单包两次采集（下载+算 hash）的最小间隔（秒），限制 refresh / GET 回源频率，防滥用
    min_collect_interval_seconds: int
    # 服务启动时是否立即采集一次（仅 interval 模式；cron 始终按表达式首次触发）
    run_on_startup: bool


@dataclass(frozen=True)
class AppConfig:
    """应用根配置，聚合各子配置"""

    server: ServerConfig
    http: HttpConfig
    qq: QQConfig
    database: DatabaseConfig
    github: GithubConfig
    scheduler: SchedulerConfig


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
    database_data: dict[str, Any] = data["database"]
    scheduler_data: dict[str, Any] = data["scheduler"]

    # sqlite_path 相对路径以配置文件所在目录（项目根）为基准展开为绝对路径
    base_dir: Path = config_path.resolve().parent
    sqlite_path: Path = Path(str(database_data["sqlite_path"]))
    if not sqlite_path.is_absolute():
        sqlite_path = base_dir / sqlite_path

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
            retry_max_attempts=int(http_data["retry_max_attempts"]),
            retry_backoff_seconds=float(http_data["retry_backoff_seconds"]),
        ),
        qq=QQConfig(
            origin=str(qq_data["origin"]),
            cookie_url=str(qq_data["cookie_url"]),
            sign_url=str(qq_data["sign_url"]),
            oidb_command=str(qq_data["oidb_command"]),
            oidb_service_type=int(qq_data["oidb_service_type"]),
        ),
        database=DatabaseConfig(
            sqlite_path=sqlite_path,
            hash_cache_ttl_seconds=int(database_data["hash_cache_ttl_seconds"]),
        ),
        github=GithubConfig(
            # 环境变量优先于配置文件，避免敏感凭证落入仓库
            token=os.environ.get("GITHUB_TOKEN")
            or (
                str(data["github"]["token"])
                if data.get("github", {}).get("token")
                else None
            )
        ),
        scheduler=SchedulerConfig(
            enabled=bool(scheduler_data["enabled"]),
            timezone=str(scheduler_data["timezone"]),
            jitter_seconds=int(scheduler_data["jitter_seconds"]),
            misfire_grace_seconds=int(scheduler_data["misfire_grace_seconds"]),
            min_collect_interval_seconds=int(
                scheduler_data["min_collect_interval_seconds"]
            ),
            run_on_startup=bool(scheduler_data["run_on_startup"]),
        ),
    )


config: AppConfig = load_config()
