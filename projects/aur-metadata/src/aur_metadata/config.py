"""TOML 配置加载模块"""

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_CONFIG_ENV_VAR = "APP_CONFIG"
_DEFAULT_CONFIG_PATH = Path("configs/config.toml")
_PACKAGES_ENV_VAR = "APP_PACKAGES"
_DEFAULT_PACKAGES_PATH = Path("configs/packages.toml")


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
    # GET /{name} 命中 DB 快照的最大年龄（秒）；超过则触发后台异步刷新
    version_stale_seconds: int


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
    # 单包两次采集的最小间隔（秒），限制手动刷新 / 后台刷新触发频率，防滥用
    min_collect_interval_seconds: int
    # 服务启动时是否立即采集一次（仅 interval 模式；cron 始终按表达式首次触发）
    run_on_startup: bool


@dataclass(frozen=True)
class PackageConfig:
    """单个包的采集配置（packages.toml 的 ``[[packages]]`` 项）。

    本类只做结构层校验（字段齐全、类型正确、调度二选一）；涉及运行时
    注册表的校验（parser_type / archs / cron 语法）在 package_seeder 完成，
    避免 config 层反向依赖 constants/parsers 造成循环导入。
    """

    name: str
    parser_type: str
    fetch_url: str
    archs: list[str]
    parser_config: dict[str, Any]
    enabled: bool
    interval_seconds: int | None
    cron_expr: str | None
    description: str | None

    @property
    def schedule_type(self) -> str:
        """调度模式：由二选一字段派生（加载期保证恰好一个非空）"""
        return "cron" if self.cron_expr is not None else "interval"


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

    路径解析优先级：显式参数 > 环境变量 ``APP_CONFIG`` > 当前目录
    ``configs/config.toml``。配置内的相对路径（如 ``sqlite_path``）
    以配置文件所在目录为基准展开。
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

    # sqlite_path 相对路径以配置文件所在目录为基准展开为绝对路径
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
            version_stale_seconds=int(database_data["version_stale_seconds"]),
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


def load_packages(path: Path | str | None = None) -> list[PackageConfig]:
    """加载包采集配置文件（TOML，``[[packages]]`` 数组）。

    路径解析优先级：显式参数 > 环境变量 ``APP_PACKAGES`` > 当前目录
    ``configs/packages.toml``。结构错误（缺字段、类型不对、调度字段
    缺失/双填、name 重复、未知键）统一收集后抛 ``ValueError``，启动即
    失败——配置文件是开发者维护的受信来源，错误应显式暴露而非静默跳过。
    """
    packages_path: Path = (
        Path(path)
        if path is not None
        else Path(os.environ.get(_PACKAGES_ENV_VAR, _DEFAULT_PACKAGES_PATH))
    )
    with open(packages_path, "rb") as f:
        data: dict[str, Any] = tomllib.load(f)

    # 键整体缺失（拼错顶层键 / 文件被清空）直接报错：静默降级成空包列表
    # 会让全部 DB 包沦为孤儿、服务空转；显式写 ``packages = []`` 才表示无托管包
    if "packages" not in data:
        raise ValueError(f"包配置文件 {packages_path} 缺少 [[packages]] 数组")
    raw_packages: list[dict[str, Any]] = data["packages"]
    errors: list[str] = []
    if not isinstance(raw_packages, list):
        errors.append(f"{packages_path}: [[packages]] 必须为数组")
        raw_packages = []
    packages: list[PackageConfig] = []
    seen_names: set[str] = set()

    for idx, item in enumerate(raw_packages):
        if not isinstance(item, dict):  # tomllib 保证为 dict，防御性分支
            errors.append(f"packages[{idx}]: 必须是表（table）")
            continue
        label: str = f"packages[{idx}](name={item.get('name', '?')!r})"

        unknown_keys: set[str] = set(item) - {
            "name",
            "parser_type",
            "fetch_url",
            "archs",
            "parser_config",
            "enabled",
            "interval_seconds",
            "cron_expr",
            "description",
        }
        if unknown_keys:
            errors.append(f"{label}: 未知字段 {sorted(unknown_keys)}")

        raw_name: Any = item.get("name")
        name: str = raw_name if isinstance(raw_name, str) else ""
        if not name.strip():
            errors.append(f"{label}: name 必须为非空字符串")
            continue
        label = f"packages[{idx}](name={name!r})"
        if name in seen_names:
            errors.append(f"{label}: name 重复")
            continue
        seen_names.add(name)

        parser_type: str | None = item.get("parser_type")
        if not isinstance(parser_type, str) or not parser_type:
            errors.append(f"{label}: parser_type 必须为非空字符串")
            continue

        fetch_url: str | None = item.get("fetch_url")
        if not isinstance(fetch_url, str) or not fetch_url:
            errors.append(f"{label}: fetch_url 必须为非空字符串")
            continue

        archs: list[Any] | None = item.get("archs")
        if (
            not isinstance(archs, list)
            or not archs
            or not all(isinstance(a, str) and a for a in archs)
        ):
            errors.append(f"{label}: archs 必须为非空字符串数组")
            continue

        parser_config: dict[str, Any] = item.get("parser_config", {})
        if not isinstance(parser_config, dict):
            errors.append(f"{label}: parser_config 必须为表（table）")
            continue

        enabled: bool = item.get("enabled", True)
        if not isinstance(enabled, bool):
            errors.append(f"{label}: enabled 必须为布尔值")
            continue

        description: str | None = item.get("description")
        if description is not None and not isinstance(description, str):
            errors.append(f"{label}: description 必须为字符串")
            continue

        interval_seconds: int | None = item.get("interval_seconds")
        cron_expr: str | None = item.get("cron_expr")
        if (interval_seconds is None) == (cron_expr is None):
            errors.append(f"{label}: interval_seconds 与 cron_expr 必须恰好填写一个")
            continue
        if interval_seconds is not None:
            # isinstance(bool) 排除 TOML 布尔混入整数位
            if (
                not isinstance(interval_seconds, int)
                or isinstance(interval_seconds, bool)
                or interval_seconds <= 0
            ):
                errors.append(f"{label}: interval_seconds 必须为正整数")
                continue
        elif not isinstance(cron_expr, str) or not cron_expr:
            errors.append(f"{label}: cron_expr 必须为非空字符串")
            continue

        packages.append(
            PackageConfig(
                name=name,
                parser_type=parser_type,
                fetch_url=fetch_url,
                archs=archs,
                parser_config=parser_config,
                enabled=enabled,
                interval_seconds=interval_seconds,
                cron_expr=cron_expr,
                description=description,
            )
        )

    if errors:
        raise ValueError(
            f"包配置文件 {packages_path} 存在错误：\n- " + "\n- ".join(errors)
        )
    return packages
