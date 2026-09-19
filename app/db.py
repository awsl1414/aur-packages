"""Tortoise ORM 初始化与 schema 装载。

schema.sql 是数据库结构的事实来源（含 STRICT 表、视图、跨字段 CHECK），
不使用 Tortoise.generate_schema（对 STRICT 表 + 视图生成不可靠）。
首次启动检测到 packages 表缺失时，逐条执行 schema.sql 完成建库；
包定义的种子由 package_seeder 从 packages.toml 同步，本文件不含数据。
"""

import logging
import re
from pathlib import Path

from tortoise import Tortoise, connections

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SCHEMA_PATH = _PROJECT_ROOT / "db" / "schema.sql"


def get_db_url(sqlite_path: Path) -> str:
    """构造 Tortoise 的 sqlite 连接 URL（路径需为绝对路径）"""
    return f"sqlite://{sqlite_path}"


def build_tortoise_config(db_url: str) -> dict[str, dict[str, object]]:
    """构造 Tortoise.init 所需的配置字典"""
    return {
        "connections": {"default": db_url},
        "apps": {"models": {"models": ["app.models"], "default_connection": "default"}},
    }


def _split_sql(sql: str) -> list[str]:
    """移除 ``--`` 行注释后按 ``;`` 切分为独立语句。

    schema.sql 无字符串字面量内分号，简单切分即可；先去注释避免注释中的 ``;`` 干扰。
    """
    cleaned: str = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
    return [stmt.strip() for stmt in cleaned.split(";") if stmt.strip()]


async def init_db(sqlite_path: Path) -> None:
    """初始化数据库：建连接 → 开外键 → 首启执行 schema.sql 建库。

    以 ``packages`` 表是否存在判定是否首次启动；已初始化则跳过建表。
    schema 演进采用**删库重建**：采集结果可由定时任务再生，故升级 schema 时
    直接删除 ``data/aur_packages.db`` 重启即可，不做增量列迁移。

    启用全局 fallback：tortoise 1.1 用 contextvar 追踪当前 context，而本服务的
    ORM 调用分散在 lifespan 子任务（调度器）与 uvicorn 请求任务两类上下文——
    请求任务不继承 lifespan 设置的 contextvar。``_enable_global_fallback`` 让
    contextvar 为空时回退到全局 context，使两类任务都能访问同一连接池。
    """
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    await Tortoise.init(
        config=build_tortoise_config(get_db_url(sqlite_path)),
        _enable_global_fallback=True,
    )

    conn = connections.get("default")
    await conn.execute_query("PRAGMA foreign_keys = ON;")

    _, rows = await conn.execute_query(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'packages';"
    )
    if rows:
        logger.info("数据库已存在，跳过建表")
        return

    logger.info("首次启动，执行 schema.sql 建库")
    schema: str = _SCHEMA_PATH.read_text(encoding="utf-8")
    for stmt in _split_sql(schema):
        await conn.execute_query(stmt)


async def close_db() -> None:
    """关闭所有数据库连接"""
    await Tortoise.close_connections()
