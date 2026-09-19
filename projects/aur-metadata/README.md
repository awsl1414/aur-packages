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

镜像以 **monorepo 仓库根为构建上下文**——Dockerfile 需要 COPY 根 `uv.lock` 与
各成员 `pyproject.toml` 才能完成 workspace 级 `--locked` 校验。因此必须从仓库
根构建，或显式指定上下文：

```bash
# 方式一：在仓库根执行
docker build -f projects/aur-metadata/Dockerfile -t aur-metadata .

# 方式二：在本成员目录内，显式指定上下文为仓库根
docker buildx build -f Dockerfile -t aur-metadata ../..

# 方式三：compose 已内置 context: ../..，在本成员目录内执行即可
docker compose build && docker compose up -d
```

注意：在本成员目录内直接 `docker build .` 会因上下文中没有根 `uv.lock` 而报
`COPY pyproject.toml uv.lock ./: no such file or directory`——这与 uv 会向上
查找 workspace 根不同，Docker 构建上下文完全由传入路径决定。

## 数据持久化

compose 默认把宿主的 `./data` 绑定挂载到容器的 `/app/data`（SQLite 落盘处），
docker 与 podman、rootful 与 rootless 均可用：容器入口脚本以 root 启动，先把
数据目录调整为 `PUID`/`PGID`（默认 1000）属主，再经 gosu 降权运行服务，规避
rootless podman 下容器 uid 与宿主目录属主不一致导致的
`unable to open database file`。需要匹配宿主账号时在 compose 中设置：

```yaml
environment:
  PUID: 1000
  PGID: 1000
```

注意 rootless podman 下宿主侧 DB 文件属主显示为子 uid（如 100999），属正常
映射现象；改用具名卷（`metadata-data:/app/data`）则无此现象。

## 开发

```bash
uv run pytest       # 运行测试（本成员目录内）
```
