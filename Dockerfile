FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# 依赖层（缓存友好：仅当 pyproject.toml/uv.lock 变化时重建）
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 源码层
COPY main.py ./
COPY app/ ./app/
COPY config.toml ./

# 默认指向镜像内 config.toml；compose 可通过环境变量覆盖
ENV AUR_PACKAGES_HELPER_CONFIG=/app/config.toml

EXPOSE 8000

CMD ["uv", "run", "main.py"]
