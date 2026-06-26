# AUR 包自动更新工具

> 自动化 Arch Linux AUR 包版本更新工具

[![Python](https://img.shields.io/badge/Python-3.13%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 特性

- 自动获取最新版本并更新 PKGBUILD
- 多架构支持：x86_64、aarch64、loong64
- 多算法校验和自动计算（支持 BLAKE2b、SHA512、SHA256）
- 基于 aria2c 的多连接分片下载
- 插件化解析器设计，易于扩展

## 快速开始

```bash
git clone https://github.com/awsl1414/aur-packages.git
cd aur-packages

# 安装系统依赖
sudo pacman -S aria2   # 或 sudo apt install aria2

# 安装 Python 依赖
pip install uv
uv sync

# 运行（在仓库根目录执行）
uv run scripts/main.py              # 更新所有包
uv run scripts/main.py --package qq # 更新指定包
uv run scripts/main.py --list       # 列出所有包
```

## 支持的包

| 包名 | 说明 |
|------|------|
| `linuxqq-nt` | QQ Linux |
| `navicat17-premium-zh-cn` | Navicat Premium 中文版 |
| `trae` | Trae AI IDE 国际版（中国 CDN） |
| `trae-sg` | Trae AI IDE 国际版（新加坡 CDN） |
| `trae-us` | Trae AI IDE 国际版（美国 CDN） |
| `trae-cn` | Trae AI IDE 国内版（独立产品，非国际版 CDN 变体） |

## 开发

```bash
uv run pytest              # 运行测试
uv run ty check scripts/   # 类型检查
uv sync                    # 同步依赖
```

## 技术栈

- Python 3.13+ / uv
- aria2c (多线程下载)
- httpx (异步 HTTP)
- pydantic (数据验证)

## 贡献

欢迎贡献！请阅读 [贡献指南](CONTRIBUTING.md)。

## 许可证

MIT License
