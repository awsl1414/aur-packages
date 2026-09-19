# AGENTS.md

@README.md
@.claude/rules/type-hints.md
@.claude/rules/comments.md

## 项目定位

本服务为 aur-auto-update 提供应用版本、文件 hash 等元数据，基于 FastAPI + Tortoise ORM（SQLite）+ APScheduler 实现。包配置以 SQLite `packages` 表为唯一来源，定时采集版本与 hash 落库；版本与 hash 为两个独立采集域（各自独立事务，版本先行落库，hash 下载失败不影响版本可用性）。查询接口纯读 DB，快照过期时后台异步刷新。

## 目录结构

```
src/aur_metadata/
├── cli.py          # 入口：create_app 工厂 + main() CLI（--config/--packages/--host/--port）
├── config.py       # TOML 配置加载（dataclass，经构造函数注入，无模块级单例）
├── db/             # Tortoise 初始化 + schema.sql（包内数据文件，importlib.resources 加载）
├── models/         # ORM 模型（字段须与 db/schema.sql 手工对齐）
├── fetcher.py      # httpx 封装：重试/限流/GitHub token/流式多 hash（HttpConfig 注入）
├── parsers/        # 上游解析器（BaseParser(app_config) 注入运行配置；registry 注册 parser_type）
├── services/       # 采集编排（package_service / schedule_service / package_seeder / registry_loader）
├── registry.py     # 内存包注册表
├── schemas.py      # Pydantic 响应模型
├── response.py     # ApiResponse[T] 统一包装 + BizError + ErrorCode
├── api/            # FastAPI 路由（deps.py 依赖注入 + v1/packages.py）
├── constants/      # 与环境无关的枚举（ArchEnum, HashAlgorithmEnum）
└── utils/          # 多算法 hash builder、deb（ar/control.tar）解析
```

## 开发命令

```bash
# uv workspace 成员，依赖由根 uv.lock 管理；
# 启动服务可在仓库根（uv run --package aur-metadata aur-metadata）或本成员目录内执行

# 本成员目录内：
uv run aur-metadata      # 启动服务
uv run pytest            # 运行测试
uv run pytest tests/     # 运行指定目录

# 代码检查（ruff/ty 配置在仓库根 pyproject，仓库根执行）
#   uv run ruff check projects/
#   uv run ty check projects/
```

**重要**: 项目统一使用 `uv` 管理和运行，禁止显式使用 `python` 命令（特殊情况除外）。

## 注意事项

- 项目使用 uv 统一管理运行环境，禁止显式使用 `python` 命令
- 项目使用带包名前缀的绝对导入（`from aur_metadata.fetcher import Fetcher`）
- Python 版本要求 >= 3.13
- 所有函数和方法必须包含完整的类型注解（详见 @.claude/rules/type-hints.md）
- 运行配置经构造函数显式注入（`AppConfig`/`HttpConfig`/`QQConfig` 等），禁止模块级读配置、禁止 import 即有副作用
- 配置路径解析：`--config` 参数 > `APP_CONFIG` 环境变量 > 默认搜索路径（成员目录 `configs/config.toml` → 仓库根 `projects/aur-metadata/configs/config.toml`，`packages.toml` 同理）；配置内的相对路径（如 `sqlite_path`）以命中的配置文件所在目录为基准解析
- Docker 构建**上下文必须是仓库根**（Dockerfile 需 COPY 根 `uv.lock` 与各成员 pyproject）：仓库根执行 `docker build -f projects/aur-metadata/Dockerfile .`，或成员目录内 `docker build -f Dockerfile ../..`；在成员目录内直接 `docker build .` 会因上下文缺根 `uv.lock` 而失败
- 数据持久化使用具名卷 `metadata-data`（镜像内已预置 `/app/data` 属主为容器运行用户 uid 1000，引擎首挂自动继承）；**不要**改为宿主目录绑定挂载——rootless 运行时（docker/podman 均然）的 user namespace 会把容器 uid 映射为子 uid，导致 `unable to open database file`
- schema 演进采用**删库重建**：采集结果可由定时任务再生，升级 schema 时直接删除数据文件重启，不做增量迁移；修改 `db/schema.sql` 时须同步对齐 `models/` 的 ORM 字段
