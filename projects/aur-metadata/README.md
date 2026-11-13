# aur-metadata

> AUR 包元数据服务：追踪上游版本与下载链接，供 [aur-auto-update](../aur-auto-update/) 查询

[![Python](https://img.shields.io/badge/Python-3.13%2B-blue)](https://www.python.org/)

## 简介

`aur-metadata` 是本 monorepo 的服务端成员，负责获取应用版本与下载链接，供 `aur-auto-update` 在更新 PKGBUILD 时调用；校验和由 `aur-auto-update` 下载安装包后本地计算。

支持定时采集各包版本与下载链接并落库 SQLite；查询接口只读快照、不触发采集（鉴权类源仅实时签名 RPC 生成可直接下载链接，失败降级）。每包由独立 task 定时采集，迟到任务不丢弃；快照新鲜度由采集周期保证。

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
uv run aur-metadata debug-extract qq                      # 按包配置试提取版本（调试 packages.toml 规则用）
uv run aur-metadata healthcheck                           # 探测自身端口是否就绪（容器 HEALTHCHECK 用）
```

默认配置路径解析顺序：`--config` 参数 > 环境变量 `APP_CONFIG` > 依次探测
`configs/config.toml`（成员目录）与 `projects/aur-metadata/configs/config.toml`
（仓库根）。

服务启动后访问 `http://127.0.0.1:8000/docs` 查看交互式 API 文档，路由规范见 [docs/api.md](docs/api.md)。

## 配置文件

| 文件 | 用途 |
| ---- | ---- |
| `configs/config.toml` | 本地开发配置（监听地址、HTTP 参数、QQ 签名、数据库、调度器） |
| `configs/config.docker.toml` | 容器部署配置（`0.0.0.0` 监听 + 挂载目录内数据库路径） |
| `configs/packages.toml` | 包采集定义（`[[packages]]` 数组，启动时幂等同步进 DB） |

配置内的相对路径以配置文件所在目录为基准解析；环境变量 `APP_CONFIG`/`APP_PACKAGES`/`GITHUB_TOKEN` 可覆盖对应配置。

## Docker 部署

### 使用已发布镜像

推送到 `dev` 时自动构建并推送多架构镜像（linux/amd64、linux/arm64）。打哪些
tag 取决于 `pyproject.toml` 的版本号是否已发布过：

| 情况 | tag |
| ---- | --- |
| 版本号是新的（首次出现） | `v<版本号>` 与 `latest` |
| 版本号已存在（改代码未升版本） | `dev` 与 `dev-<短哈希>`，不覆盖 `latest` |

所以发版流程是：改完代码 → 升 `pyproject.toml` 版本 → 推 `dev` → 拿到
`v<版本号>` 镜像。未升版本的提交只产出 `dev` 标签，便于验证而不影响用户。

```bash
docker pull awsl1414/aur-metadata:latest          # 最新发布版
docker pull awsl1414/aur-metadata:v1.0.3          # 锁定版本
docker pull awsl1414/aur-metadata:dev             # dev 分支最新构建
docker pull ghcr.io/awsl1414/aur-metadata:latest  # GitHub Container Registry
```

运行（数据落到当前目录的 `data/`，无需预先创建）：

```bash
docker run -d --name aur-metadata \
  -p 8000:8000 \
  -v "$PWD/configs/config.docker.toml:/app/configs/config.docker.toml:ro" \
  -v "$PWD/data:/app/data" \
  -e GITHUB_TOKEN=<token> \
  awsl1414/aur-metadata:latest
```

`GITHUB_TOKEN` 可省，但匿名调用 `api.github.com` 限流 60 次/时，`fetch_url`
指向 GitHub API 的包（见 `configs/packages.toml`）会频繁采集失败。

### 本地构建镜像

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

国内网络拉取 `python:3.13-slim` 与 `ghcr.io/astral-sh/uv` 可能很慢或超时。可用
镜像加速服务替换基础镜像地址，本地构建验证时不必改 Dockerfile：

```bash
sed -e 's|^FROM python:|FROM <加速前缀>/library/python:|' \
    -e 's|ghcr.io/astral-sh/uv|<加速前缀>/astral-sh/uv|' \
    projects/aur-metadata/Dockerfile > /tmp/Dockerfile.fast
docker build -f /tmp/Dockerfile.fast -t aur-metadata .
```

注意：在本成员目录内直接 `docker build .` 会因上下文中没有根 `uv.lock` 而报
`COPY pyproject.toml uv.lock ./: no such file or directory`——这与 uv 会向上
查找 workspace 根不同，Docker 构建上下文完全由传入路径决定。

## 数据持久化

SQLite 落在宿主目录 `./data`。目录不用手动创建，权限要求取决于 Docker 的运行模式：

**rootful Docker**：容器内的进程是 root，入口脚本会建目录、把属主改成运行用户
（uid 1000），再降权启动。宿主侧不需要任何操作。

**rootless Docker 或 podman**：容器拿不到 `CAP_CHOWN`，且容器 uid 会被映射成
宿主子 uid，无法修改宿主目录属主。需要先让目录可写：

```bash
mkdir -p data && chmod 0777 data
```

权限不满足时容器不会反复重启，而是打印上面需要的命令后退出。

## 开发

```bash
uv run pytest       # 运行测试（本成员目录内）
```
