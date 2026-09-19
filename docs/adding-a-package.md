# 添加新软件包

本文档是添加新包流程的唯一来源：从 PKGBUILD 编写、元数据注册到 updater 配置的完整三步。

## 第 1 步：编写 PKGBUILD

在 `packages/` 目录中创建以包名命名的子目录，编写 PKGBUILD。

- **必须遵守** [打包规范](packaging-guide.md)（版本、依赖、校验和、source 声明等）
- 本地源文件（`.sh`、`.desktop`、`.install`）列入 `source=()` 后，**修改内容必须同步更新 PKGBUILD 中对应的校验和**（`b2sums`、`sha512sums`），否则 makepkg 构建失败——原因与案例见 [已知问题](troubleshooting.md)

## 第 2 步：注册元数据采集

在 `projects/aur-metadata/configs/packages.toml` 中添加 `[[packages]]` 采集定义（版本源、架构、调度周期）。服务启动时会幂等同步进 DB `packages` 表，此即包注册；改完可用 `uv run aur-metadata debug-extract <包名>` 试提取调试。

选择解析方式（按优先级）：

1. **`parser_type = "rule"`**：简单数据源（HTML/JSON 的单点提取），用声明式规则表达（xpath/css/jmespath/re，见 `src/aur_metadata/parsers/rule.py`）
2. **`parser_type = "rule-deb"`**：版本取自 deb 安装包头部、URL 由规则提取的组合
3. **专属解析器**：以上都表达不了时（鉴权下载、跨架构一致性校验等），在 `src/aur_metadata/parsers/` 实现并注册进 `_PARSER_REGISTRY`

字段说明与 TOML 子表头注意事项见 `configs/packages.toml` 文件头注释。

## 第 3 步：配置 updater

在 `config.yaml`（仓库根）中添加包配置：

| 字段 | 必填 | 说明 |
| ---- | ---- | ---- |
| `name` | ✓ | metadata 注册的包名 |
| `pkgbuild` | ✓ | PKGBUILD 路径（相对 `config.yaml` 所在目录） |
| `arch` | ✓ | 架构列表，须与 `packages.toml` 的 `archs` 一致 |
| `update_source_url` | — | 覆盖自动从 PKGBUILD 提取的 source URL |
| `enable` | — | 是否启用该包（默认 true） |
| `hash_algorithm` | — | 包级哈希算法覆盖，默认继承 `settings.hash_algorithm` |

## 验证

```bash
# 注册检查：metadata 侧试提取
uv run aur-metadata debug-extract <包名>

# 更新链路：updater 侧看到包并可更新
uv run --package aur-auto-update aur-auto-update --list
uv run --package aur-auto-update aur-auto-update -p <包名>
```
