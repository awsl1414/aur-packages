# AUR Packages Helper

> 为 [aur-packages](https://github.com/awsl1414/aur-packages) 提供应用版本、文件 hash 等信息的服务

[![Python](https://img.shields.io/badge/Python-3.13%2B-blue)](https://www.python.org/)

## 简介

`aur-packages-helper` 是 [aur-packages](https://github.com/awsl1414/aur-packages) 的配套服务，负责获取应用版本、计算文件 hash 等辅助功能，供 `aur-packages` 在更新 PKGBUILD 时调用。

支持定时采集各包版本与文件 hash 并落库 SQLite；查询接口纯读数据库（版本与 hash 独立采集、独立落库，版本先行永不被下载失败连坐），快照过期时后台异步刷新，永不阻塞响应。

## 技术栈

- Python 3.13+ / uv
- FastAPI（Web 服务）
- Tortoise ORM（数据持久化，SQLite）
- APScheduler（定时采集调度）

## 开发

```bash
uv sync          # 同步依赖
uv run main.py   # 启动服务
```

服务启动后访问 `http://127.0.0.1:8000/docs` 查看交互式 API 文档，路由规范见 [docs/api.md](docs/api.md)。
