# AGENTS.md

@README.md
@docs/packaging-guide.md
@.claude/rules/type-hints.md
@.claude/rules/comments.md

## 项目结构（uv workspace monorepo）

本仓库是 uv workspace monorepo，根 `pyproject.toml` 为虚拟 workspace 根（不构建、不安装），Python 应用统一位于 `projects/` 下，均为 src 布局 + `uv_build` 后端的 packaged application：

| 成员 | 说明 | 入口 |
| ---- | ---- | ---- |
| `projects/aur-auto-update` | AUR 包自动更新工具，消费 aur-metadata 的 API 更新 PKGBUILD | `aur_auto_update.cli:main` → `aur-auto-update` |
| `projects/aur-metadata` | 包元数据服务（FastAPI + Tortoise ORM/SQLite + APScheduler），追踪上游版本、计算文件 hash | `aur_metadata.cli:main` → `aur-metadata` |

非 Python 资产在仓库根：`packages/`（AUR PKGBUILD）、`config.yaml`（updater 配置）、`structure/`、`docs/`。

## 开发命令

```bash
# uv workspace：依赖统一由根 uv.lock 管理

uv sync                                          # 同步依赖（仓库根执行）

# aur-auto-update（仓库根执行）
uv run --package aur-auto-update aur-auto-update --all        # 更新所有包
uv run --package aur-auto-update aur-auto-update -p linuxqq-nt # 更新指定包
uv run --package aur-auto-update aur-auto-update --list       # 列出所有可用包

# aur-metadata（仓库根或成员目录内均可执行，默认配置路径自动搜索）
uv run --package aur-metadata aur-metadata   # 从仓库根执行
cd projects/aur-metadata && uv run aur-metadata  # 或从成员目录执行

# 测试（pytest 配置在各成员 pyproject 中，须在成员目录内执行）
cd projects/aur-auto-update && uv run pytest
cd projects/aur-metadata && uv run pytest

# 代码检查（ruff/ty 配置在根 pyproject，仓库根执行）
uv run ruff check projects/
uv run ty check projects/
```

**重要**:

- 项目统一使用 `uv` 管理和运行，禁止显式使用 `python` 命令（特殊情况除外）
- 添加依赖：运行依赖进对应成员 `pyproject.toml`（`uv add --package <member> <pkg>`），开发依赖进成员 `dev` 组，ruff/ty 进根 `dev` 组
- 导入使用带包名前缀的绝对导入（如 `from aur_auto_update.core.package_updater import PackageUpdater`、`from aur_metadata.fetcher import Fetcher`）
- Python 版本要求 >= 3.13

## 添加新软件包

完整三步流程（PKGBUILD → packages.toml 注册 → config.yaml 配置）见 @docs/adding-a-package.md，为该流程的唯一来源，不在本文件重复。

## Commit 规范

项目使用 [Conventional Commits 1.0.0](https://www.conventionalcommits.org/) 规范，通过 `.githooks/commit-msg` 自动校验。格式与类型表见 [CONTRIBUTING.md](CONTRIBUTING.md)，不在本文件重复。

## 注意事项

- **编辑或创建 PKGBUILD 时必须遵守 @docs/packaging-guide.md 中的规范**
- **修改 `packages/` 中的本地源文件（如 `.sh`、`.desktop`、`.install`）后，必须同步更新 PKGBUILD 中对应的校验和（如 `b2sums`、`sha512sums`）**，否则 makepkg 校验哈希失败、构建中断（机制与案例见 @docs/troubleshooting.md「通用」节）
- **包运行时/构建问题参见 @docs/troubleshooting.md**，包含已知的捆绑库冲突、缓存问题等及其解决方案
- 运行配置锚定原则：配置内的相对路径一律相对配置文件所在目录解析（updater 的 `config.yaml` 在仓库根；metadata 的 `configs/config.toml` 在成员内）；包内静态资源（如 schema.sql）用 `importlib.resources` 加载，禁止 `__file__` 上溯定位
- 模块导入不得产生副作用：运行配置经构造函数显式注入，禁止模块级读配置/建应用
- **aur-auto-update 的下载器依赖 aria2c**，运行前需确保系统已安装 aria2（`sudo pacman -S aria2`）
- PKGBUILD 文件路径相对于仓库根目录（`aur-packages/`）

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
