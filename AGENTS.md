# AGENTS.md

@README.md
@CONTRIBUTING.md
@.claude/rules/type-hints.md
@.claude/rules/comments.md

## 项目定位

本服务为 [aur-packages](https://github.com/awsl1414/aur-packages) 提供应用版本、文件 hash 等信息，基于 FastAPI + Tortoise ORM 实现。

## 开发命令

```bash
# 以下命令均在仓库根目录执行（uv 项目根 = 仓库根）

# 启动服务
uv run main.py

# 依赖管理
uv sync                  # 同步依赖
uv add <package>         # 添加运行依赖
uv add --dev <package>   # 添加开发依赖

# 代码检查
uv run ruff check .      # 代码规范检查
uv run ruff format .     # 代码格式化
uv run ty check .        # 类型检查

# 测试
uv run pytest            # 运行所有测试
uv run pytest tests/     # 运行指定目录
```

**重要**: 项目统一使用 `uv` 管理和运行，禁止显式使用 `python` 命令（特殊情况除外）。

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

- 项目使用 uv 统一管理运行环境，禁止显式使用 `python` 命令
- 项目使用绝对导入
- Python 版本要求 >= 3.13
- 所有函数和方法必须包含完整的类型注解（详见 @.claude/rules/type-hints.md）
- Git hooks 已配置为 `.githooks/` 目录，首次克隆后无需手动安装
