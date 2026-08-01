# AGENTS.md

@README.md
@scripts/README.md
@docs/packaging-guide.md
@.claude/rules/type-hints.md

## 开发命令

```bash
# 以下命令均在仓库根目录执行（uv 项目根 = 仓库根）

# 运行程序（使用 uv）
uv run scripts/main.py                    # 更新所有包
uv run scripts/main.py --package linuxqq-nt  # 更新指定包
uv run scripts/main.py --list             # 列出所有可用包

# 运行测试
uv run pytest                                    # 运行所有测试
uv run pytest scripts/tests/fetcher/test_fetcher.py  # 运行单个测试文件

# 依赖管理
uv sync                                          # 同步依赖
uv add <package>                                 # 添加新依赖
uv remove <package>                              # 移除依赖

# 类型检查
uv run ty check scripts/
```

**重要**: 项目统一使用 `uv` 管理和运行，禁止显式使用 `python` 命令（特殊情况除外）。

## 添加新软件包

1. 在 `aur-packages-helper` 的 DB 中注册包（`name`、`parser_type`、`fetch_url`、`archs`、`parser_config`），由 helper 服务端完成上游解析
2. 在 `config.yaml` 中添加包配置（`name` 填 helper 注册的包名，含 `pkgbuild` 路径与 `arch`）
3. 在 `packages/` 目录中创建对应的 PKGBUILD 文件

## Commit 规范

项目使用 [Conventional Commits 1.0.0](https://www.conventionalcommits.org/) 规范，通过 `.githooks/commit-msg` 自动校验。

格式：`<type>(<scope>): <description>`

| 类型 | 用途 |
| ------ | ------ |
| `feat` | 新功能 |
| `fix` | 修复 bug |
| `docs` | 文档变更 |
| `style` | 代码格式（不影响逻辑） |
| `refactor` | 重构（非新功能、非修复） |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `build` | 构建系统或外部依赖 |
| `ci` | CI 配置 |
| `chore` | 其他不修改 src 或 test 的变更 |
| `revert` | 回退提交 |

## 注意事项

- **编辑或创建 PKGBUILD 时必须遵守 @docs/packaging-guide.md 中的规范**
- **修改 `packages/` 中的本地源文件（如 `.sh`、`.desktop`、`.install`）后，必须同步更新 PKGBUILD 中对应的校验和（如 `b2sums`、`sha512sums`）**。本地文件被列入 `source=()` 数组，makepkg 会校验其哈希，修改内容但不更新哈希会导致构建失败
- **包运行时/构建问题参见 @docs/troubleshooting.md**，包含已知的捆绑库冲突、缓存问题等及其解决方案
- **项目使用 uv 统一管理运行环境，禁止显式使用 `python` 命令**
- 项目使用绝对导入（`from core.package_updater import PackageUpdater`），而不是相对导入
- Python 版本要求 >= 3.13
- **下载器依赖 aria2c**，运行前需确保系统已安装 aria2（`sudo pacman -S aria2`）
- PKGBUILD 文件路径相对于项目根目录（`aur-packages/`），而非 `scripts/` 目录

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
