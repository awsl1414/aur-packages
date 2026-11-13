# syntax=docker/dockerfile:1.7
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

# 运行用户固定 uid/gid（数字形式便于容器内 chown 与宿主侧排查）
ARG APP_UID=1000
ARG APP_GID=1000

WORKDIR /app

# 建立与 APP_UID 对应的账号：su/init-groups 等工具要求 uid 能在 passwd 中查到
RUN groupadd --gid "${APP_GID}" app \
    && useradd --uid "${APP_UID}" --gid "${APP_GID}" --no-create-home --shell /usr/sbin/nologin app

COPY --from=builder /app/.venv /app/.venv
COPY --chown=${APP_UID}:${APP_GID} projects/aur-metadata/configs /app/configs

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_UID=${APP_UID} \
    APP_GID=${APP_GID}

# 数据目录写权限分两种部署：
# - rootful Docker：容器内是 root，脚本改属主后降权，宿主目录不用预先处理
# - rootless Docker / podman：容器内拿不到 CAP_CHOWN，uid 也被映射成宿主子 uid，
#   宿主目录需 chmod 0777 或 chown 给运行 Docker 的用户。脚本检查后打印具体命令。
COPY --chmod=755 <<'EOF' /usr/local/bin/docker-entrypoint.sh
#!/bin/sh
set -eu

DATA_DIR=/app/data

is_root() { [ "$(id -u)" = "0" ]; }

if is_root; then
    mkdir -p "$DATA_DIR"
    chown -R "${APP_UID}:${APP_GID}" "$DATA_DIR" 2>/dev/null || true
    exec setpriv --reuid="${APP_UID}" --regid="${APP_GID}" --keep-groups "$@"
fi

mkdir -p "$DATA_DIR" 2>/dev/null || true
if ! ( : > "$DATA_DIR/.write-probe" ) 2>/dev/null; then
    cat >&2 <<MSG
ERROR: 当前用户 $(id -u) 无法写入 $DATA_DIR

rootless Docker 把容器 uid 映射成宿主子 uid，容器内无法改宿主目录属主。
在宿主机执行其一：
  chmod 0777 <宿主目录>                    # 最简单
  chown $(id -u):$(id -g) <宿主目录>       # 若宿主属主就是运行 Docker 的用户
MSG
    exit 1
fi
rm -f "$DATA_DIR/.write-probe"

exec "$@"
EOF

# 端口从配置读取，编排文件不重复写死
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD aur-metadata --config /app/configs/config.docker.toml healthcheck

EXPOSE 8000

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["aur-metadata", "--config", "/app/configs/config.docker.toml"]
