# 贡献指南

感谢你对本项目的关注！请遵循以下指南提交贡献。

## 分支策略

所有贡献都应提交到 `dev` 分支，不要直接修改 `main` 分支。

```
main  ← 稳定版本，由维护者从 dev 合并
dev   ← 日常开发，接受 PR 和直接推送
```

## 提交流程

1. Fork 并基于 `dev` 分支开发
2. 提交符合 [Conventional Commits](https://www.conventionalcommits.org/) 规范的 commit
3. 向 `dev` 分支提交 Pull Request

## Commit 规范

格式：`<type>(<scope>): <description>`

| 类型 | 用途 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复 bug |
| `docs` | 文档变更 |
| `style` | 代码格式（不影响逻辑） |
| `refactor` | 重构（非新功能、非修复） |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `build` | 构建系统或外部依赖 |
| `ci` | CI 配置 |
| `chore` | 其他变更 |
| `revert` | 回退提交 |

示例：

```
feat(qq): add loong64 architecture support
fix(navicat): resolve AppImage libsystemd conflict
docs: update packaging guide
```

## 添加新软件包

完整三步流程（PKGBUILD → packages.toml 注册 → config.yaml 配置，含解析器选型与验证命令）见 [docs/adding-a-package.md](docs/adding-a-package.md)，PKGBUILD 编写规范见 [docs/packaging-guide.md](docs/packaging-guide.md)。
