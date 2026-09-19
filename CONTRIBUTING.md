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

1. 在 `packages/` 目录中创建以包名命名的子目录，编写 `PKGBUILD` 文件，遵守 [Arch Wiki - Creating packages](https://wiki.archlinux.org/title/Creating_packages) 与 [打包规范](docs/packaging-guide.md)
2. 在 `projects/aur-metadata/configs/packages.toml` 中添加包采集定义（版本源、架构、调度周期）；如需新的解析方式，在 `projects/aur-metadata/src/aur_metadata/parsers/` 实现解析器并注册进 `_PARSER_REGISTRY`
3. 在 metadata 服务的 `packages` 表中注册包（服务启动时从 `packages.toml` 幂等同步）
4. 在 `config.yaml`（仓库根）中添加包配置（`name` 填 metadata 注册的包名）
