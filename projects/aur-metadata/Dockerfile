# syntax=docker/dockerfile:1.7
# 构建上下文为 monorepo 仓库根：
#   docker build -f projects/aur-metadata/Dockerfile .

FROM python:3.13-slim AS builder

# uv 版本与开发环境 lockfile 生成版本一致，保证 --locked 校验稳定可复现
COPY --from=ghcr.io/astral-sh/uv:0.12.16 /uv /usr/local/bin/uv

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
COPY --chown=1000:1000 projects/aur-metadata/configs /app/configs

# 预建运行数据目录并归属 uid 1000（容器内进程以该用户运行，
# 具名卷首挂载时继承目录属主）
RUN mkdir -p /app/data && chown 1000:1000 /app/data

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER 1000:1000

EXPOSE 8000

CMD ["aur-metadata", "--config", "/app/configs/config.docker.toml"]
