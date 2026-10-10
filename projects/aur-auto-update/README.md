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
├── services/           # 核心协调器（PackageUpdater：Fetch → Parse → Update）
└── utils/              # 工具函数（aria2c 下载器、哈希、URL/版本工具）
```

所有上游解析（QQ / Navicat / Trae / Zen / PyPI）统一由本仓库
`projects/aur-metadata` 的 `GET /api/v1/packages/{name}` 接口完成，本工具只
消费 `{version, urls, download_urls, hashes}` 结构：`urls` 为原始稳定链接，
写入 PKGBUILD `source_<arch>=()`（QQ 等鉴权源的签名由 DLAGENTS 在 makepkg
阶段完成）；`download_urls` 为服务端实时生成的可直接下载链接（临时签名、会
过期），仅供本地回退下载使用。metadata 未提供 hashes 时回退到本地 aria2c
下载计算（优先 `download_urls`，缺失退回 `urls`）。

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
