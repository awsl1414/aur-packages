# aur-auto-update

AUR 包自动更新工具：消费 [aur-metadata](../aur-metadata/) 的 API，自动更新 `packages/` 下 PKGBUILD 的版本号与校验和。monorepo 整体说明见根目录 [README](../../README.md)。

## 模块结构

```
src/aur_auto_update/
├── cli.py              # 命令行入口（argparse，entry point 目标）
├── config.py           # 配置加载（config.yaml → Pydantic 模型）
├── constants/          # 枚举定义（ArchEnum, HashAlgorithmEnum）
├── fetcher.py          # HTTP 客户端（httpx，查询 metadata API）
├── parsers/            # 唯一解析器（ApiParser：消费 metadata API 统一响应）
├── pkgbuild_editor.py  # PKGBUILD 编辑器（正则替换）
├── services/           # 核心协调器（PackageUpdater）+ 版本来源与 GitHub 回退
└── utils/              # 工具函数（aria2c 下载器、哈希、URL/版本工具）
```

上游解析优先由本仓库 `projects/aur-metadata` 的
`GET /api/v1/packages/{name}` 接口完成，本工具消费
`{version, urls, download_urls}` 结构：`urls` 为原始稳定链接，写入 PKGBUILD
`source_<arch>=()`（QQ 等鉴权源的签名由 DLAGENTS 在 makepkg 阶段完成）；
`download_urls` 为服务端实时生成的可直接下载链接（临时签名、会过期），仅供
本地下载使用，不写入 PKGBUILD。

校验和一律由本工具下载安装包后本地计算（优先 `download_urls`，缺失退回
`urls`），metadata 不提供 hash。

**GitHub 回退**：`config.yaml` 中配置了 `github` 段的包（当前为 zen-browser、
orca-ide、rustmusic），在 metadata 请求失败时改用本地 GitHub release 解析获取
版本与下载链接；`GITHUB_TOKEN` 从环境变量读取。未配置 `github` 的包在 metadata
失败时直接跳过。

> 契约约束：客户端要求响应**必须**含 `download_urls` 字段（缺失视为响应契约
> 违规、解析失败）。两成员同仓同步升级即可；若分开部署，须先升 metadata 再升
> updater。

## 使用

```bash
# 在仓库根目录执行
uv run --package aur-auto-update aur-auto-update             # 更新所有包
uv run --package aur-auto-update aur-auto-update -p linuxqq-nt # 更新指定包
uv run --package aur-auto-update aur-auto-update --list        # 列出所有可用包
```

`--config` 可指定配置文件路径（默认 `config.yaml`，相对当前目录）；配置内的
相对路径（`pkgbuild`、`downloads/`）以配置文件所在目录为基准解析。

## 前置依赖

- Python >= 3.13
- aria2c（用于回退多线程下载）
- uv（包管理器）
