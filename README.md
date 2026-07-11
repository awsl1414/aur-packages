# AUR Packages Helper

> 为 [aur-packages](https://github.com/awsl1414/aur-packages) 提供应用版本、文件 hash 等信息的服务

[![Python](https://img.shields.io/badge/Python-3.13%2B-blue)](https://www.python.org/)

## 简介

`aur-packages-helper` 是 [aur-packages](https://github.com/awsl1414/aur-packages) 的配套服务，负责获取应用版本、计算文件 hash 等辅助功能，供 `aur-packages` 在更新 PKGBUILD 时调用。

## 技术栈

- Python 3.13+ / uv
- FastAPI（Web 服务）
- Tortoise ORM（数据持久化）

## 开发

```bash
uv sync          # 同步依赖
uv run main.py   # 启动服务
```

服务启动后访问 `http://127.0.0.1:8000/docs` 查看交互式 API 文档，路由规范见 [docs/api.md](docs/api.md)。
