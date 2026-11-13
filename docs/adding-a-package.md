# 添加新软件包

本文档是添加新包流程的唯一来源：从 PKGBUILD 编写、元数据注册到 updater 配置的完整三步。

## 第 1 步：编写 PKGBUILD

在 `packages/` 目录中创建以包名命名的子目录，编写 PKGBUILD。

> **CI 行为**：定时更新工作流只推送「被 updater 实际改动过 PKGBUILD」的包
> （按 `git diff` 检测）——未完成注册的目录不会被自动更新，也就不会进推送矩阵。
> 但**手动全量触发** `push-to-aur` 时会扫描 `packages/*/` 全部目录并推送；
> 因此目录一旦提交，请尽快完成下面两步注册接入自动更新，或明确标注纯手动维护。

- **必须遵守** [打包规范](packaging-guide.md)（版本、依赖、校验和、source 声明等）
- 本地源文件（`.sh`、`.desktop`、`.install`）列入 `source=()` 后，**修改内容必须同步更新 PKGBUILD 中对应的校验和**（`b2sums`、`sha512sums`），否则 makepkg 构建失败——原因与案例见 [已知问题](troubleshooting.md)

## 第 2 步：注册元数据采集

在 `projects/aur-metadata/configs/packages.toml` 中添加 `[[packages]]` 采集定义（版本源、架构、调度周期）。服务启动时会幂等同步进 DB `packages` 表，此即包注册；改完可用 `uv run aur-metadata debug-extract <包名>` 试提取调试。

选择解析方式（按优先级）：

1. **`parser_type = "rule"`**：简单数据源（HTML/JSON 的单点提取），用声明式规则表达（xpath/css/jmespath/re，见 `src/aur_metadata/parsers/rule.py`）。上游有多种可选形态时，把规则写成表列表按序 fallback（`[[packages.parser_config.version]]` 重复声明）
2. **`parser_type = "rule-deb"`**：版本取自 deb 安装包头部、URL 由规则提取的组合
3. **专属解析器**：以上都表达不了时（鉴权下载、跨架构一致性校验等），在 `src/aur_metadata/parsers/` 实现并注册进 `_PARSER_REGISTRY`

字段说明与 TOML 子表头注意事项见 `configs/packages.toml` 文件头注释。

## 第 3 步：配置 updater

在 `config.yaml`（仓库根）中添加包配置：

| 字段 | 必填 | 说明 |
| ---- | ---- | ---- |
| `name` | ✓ | metadata 注册的包名 |
| `pkgbuild` | ✓ | PKGBUILD 路径（相对 `config.yaml` 所在目录） |
| `arch` | ✓ | 架构列表，须与 `packages.toml` 的 `archs` 一致。上游只发部分架构时两者都只列已发布的（如 rustmusic 的 deb 仅有 amd64） |
| `update_source_url` | — | 是否用 metadata 返回的 URL 更新 PKGBUILD 的 source 字段（默认 true；为 false 时只更新版本与校验和） |
| `enable` | — | 是否启用该包（默认 true） |
| `hash_algorithm` | — | 包级哈希算法覆盖，默认继承 `settings.hash_algorithm` |
| `github` | — | GitHub 来源包的回退配置（见下） |

`github` 段用于 metadata 服务不可用时回退到本地 release 解析，字段：

| 字段 | 必填 | 说明 |
| ---- | ---- | ---- |
| `repo` | ✓ | `owner/repo` |
| `tag` | — | 固定 release tag；留空则用 `/releases/latest` |
| `version` | ✓ | 版本提取规则（表或表数组）。`source` 为 `tag_name`/`name`，`regex` 提取，`group` 取捕获组或 `template` 拼接；多条规则按序 fallback |
| `assets` | ✓ | 架构 → asset 匹配规则。`*` 开头为后缀匹配，否则精确匹配文件名；键须覆盖 `arch` 清单 |

该段的规则与 `projects/aur-metadata/configs/packages.toml` 中的采集规则作用相同，
新增或修改 GitHub 包时两处须同步维护。

## 验证

```bash
# 注册检查：metadata 侧试提取
uv run aur-metadata debug-extract <包名>

# 更新链路：updater 侧看到包并可更新
uv run --package aur-auto-update aur-auto-update --list
uv run --package aur-auto-update aur-auto-update -p <包名>
```
