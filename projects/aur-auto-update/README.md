# aur-auto-update

AUR 包自动更新工具：消费 [aur-metadata](../aur-metadata/) 的 API，自动更新 `packages/` 下 PKGBUILD 的版本号与校验和。monorepo 整体说明见根目录 [README](../../README.md)。

## 模块结构

```
src/aur_auto_update/
├── cli.py          # 命令行入口（argparse，entry point 目标）
├── core/           # 核心协调器（PackageUpdater：Fetch → Parse → Update）
├── constants/      # 枚举定义（ArchEnum, HashAlgorithmEnum）
├── fetcher/        # HTTP 客户端（httpx，获取版本信息）
├── loaders/        # 配置加载（config.yaml → Pydantic 模型）
├── parsers/        # 唯一解析器（ApiParser：消费 metadata API 统一响应）
├── updater/        # PKGBUILD 编辑器（正则替换）
└── utils/          # 工具函数（aria2c 下载器、哈希、URL/版本工具）
```

所有上游解析（QQ / Navicat / Trae / Zen / PyPI）统一由本仓库
`projects/aur-metadata` 的 `GET /api/v1/packages/{name}` 接口完成，本工具只
消费 `{version, urls, hashes}` 结构。metadata 未提供 hashes 时回退到本地
aria2c 下载计算。

## 使用

```bash
# 在仓库根目录执行
uv run --package aur-auto-update aur-auto-update --all         # 更新所有包
uv run --package aur-auto-update aur-auto-update -p linuxqq-nt # 更新指定包
uv run --package aur-auto-update aur-auto-update --list        # 列出所有可用包
```

`--config` 可指定配置文件路径（默认 `config.yaml`，相对当前目录）；配置内的
相对路径（`pkgbuild`、`downloads/`）以配置文件所在目录为基准解析。

## 前置依赖

- Python >= 3.13
- aria2c（用于回退多线程下载）
- uv（包管理器）
