# aur-metadata

> AUR 包元数据服务：追踪上游版本、计算文件 hash，供 [aur-auto-update](../aur-auto-update/) 查询

[![Python](https://img.shields.io/badge/Python-3.13%2B-blue)](https://www.python.org/)

## 简介

`aur-metadata` 是本 monorepo 的服务端成员，负责获取应用版本、计算文件 hash，供 `aur-auto-update` 在更新 PKGBUILD 时调用。

支持定时采集各包版本与文件 hash 并落库 SQLite；查询接口纯读数据库（版本与 hash 独立采集、独立落库，版本先行永不被下载失败连坐），快照过期时后台异步刷新，永不阻塞响应。

## 技术栈

- Python 3.13+ / uv
- FastAPI（Web 服务）
- Tortoise ORM（数据持久化，SQLite）
- APScheduler（定时采集调度）

## 使用

```bash
# 仓库根或本成员目录内执行均可（默认配置路径自动搜索）
uv run aur-metadata                                       # 本成员目录内
uv run --package aur-metadata aur-metadata                # 仓库根
uv run aur-metadata --config configs/config.docker.toml   # 指定配置
uv run aur-metadata --host 0.0.0.0 --port 9000            # 覆盖监听地址
```

默认配置路径解析顺序：`--config` 参数 > 环境变量 `APP_CONFIG` > 依次探测
`configs/config.toml`（成员目录）与 `projects/aur-metadata/configs/config.toml`
（仓库根）。

服务启动后访问 `http://127.0.0.1:8000/docs` 查看交互式 API 文档，路由规范见 [docs/api.md](docs/api.md)。

## 配置文件

| 文件 | 用途 |
| ---- | ---- |
| `configs/config.toml` | 本地开发配置（监听地址、HTTP 参数、QQ 签名、数据库、调度器） |
| `configs/config.docker.toml` | 容器部署配置（`0.0.0.0` 监听 + 卷内数据库路径） |
| `configs/packages.toml` | 包采集定义（`[[packages]]` 数组，启动时幂等同步进 DB） |

配置内的相对路径以配置文件所在目录为基准解析；环境变量 `APP_CONFIG`/`APP_PACKAGES`/`GITHUB_TOKEN` 可覆盖对应配置。

## Docker 部署

```bash
# 在仓库根执行（构建上下文为 monorepo 根）
docker build -f projects/aur-metadata/Dockerfile -t aur-metadata .
docker compose -f projects/aur-metadata/compose.yaml up -d
```

## 开发

```bash
uv run pytest       # 运行测试（本成员目录内）
```
