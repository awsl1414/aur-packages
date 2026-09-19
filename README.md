# aur-packages

> Arch Linux AUR 包维护 monorepo：包元数据服务 + 自动更新工具 + PKGBUILD 仓库

[![Python](https://img.shields.io/badge/Python-3.13%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

本仓库为 uv workspace monorepo，包含两个 Python 应用与 AUR 包资产：

| 项目 | 说明 |
| ---- | ---- |
| [`projects/aur-metadata`](projects/aur-metadata/) | 包元数据服务：定时追踪上游版本、计算文件 hash（b2/sha256/sha512），经 HTTP API 供更新工具查询 |
| [`projects/aur-auto-update`](projects/aur-auto-update/) | AUR 包自动更新工具：消费 aur-metadata 的 API，自动更新 `packages/` 下 PKGBUILD 的版本号与校验和 |
| `packages/` | AUR PKGBUILD 与本地源文件（由 CI 在版本更新后自动发布到 AUR） |

## 快速开始

```bash
git clone https://github.com/awsl1414/aur-packages.git
cd aur-packages

# 安装系统依赖（aur-auto-update 的回退下载器）
sudo pacman -S aria2   # 或 sudo apt install aria2

# 同步依赖（uv workspace，单 uv.lock 管理全部成员）
uv sync

# 更新所有包（仓库根执行）
uv run --package aur-auto-update aur-auto-update --all

# 启动元数据服务（仓库根或成员目录内执行，默认 :8000）
uv run --package aur-metadata aur-metadata
```

服务启动后访问 `http://127.0.0.1:8000/docs` 查看交互式 API 文档。

## 开发

```bash
cd projects/aur-auto-update && uv run pytest   # 更新工具测试
cd projects/aur-metadata && uv run pytest      # 元数据服务测试
uv run ruff check projects/                    # 代码规范
uv run ty check projects/                      # 类型检查
```

## 贡献

欢迎贡献！请阅读 [贡献指南](CONTRIBUTING.md)。

## 许可证

MIT License
