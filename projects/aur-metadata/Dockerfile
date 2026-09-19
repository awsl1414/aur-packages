# syntax=docker/dockerfile:1
# 构建上下文为 monorepo 仓库根：
#   docker build -f projects/aur-metadata/Dockerfile .

FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

ENV UV_LINK_MODE=copy

# 先拷贝 workspace 元数据以利用层缓存，再拷贝成员内容
# （所有成员的 pyproject 都属于 workspace 定义，缺一会导致 --locked 校验失败）
COPY pyproject.toml uv.lock ./
COPY projects/aur-auto-update/pyproject.toml projects/aur-auto-update/pyproject.toml
COPY projects/aur-metadata/ projects/aur-metadata/

# --no-editable：产物自包含，运行时镜像无需携带源码
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync \
        --locked \
        --package aur-metadata \
        --no-dev \
        --no-editable


FROM python:3.13-slim

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY projects/aur-metadata/configs /app/configs
COPY projects/aur-metadata/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

# gosu 供 entrypoint 在 root 启动后降权到 PUID/PGID 运行服务
RUN chmod +x /usr/local/bin/docker-entrypoint.sh && \
    apt-get update && \
    apt-get install -y --no-install-recommends gosu && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /app/data

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# 不设 USER：entrypoint 以 root 启动、调整数据目录属主后经 gosu 降权，
# 以兼容 docker/podman 在 rootful/rootless 下的不同 uid 映射（见 entrypoint 注释）
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["aur-metadata", "--config", "/app/configs/config.docker.toml"]
