#!/bin/sh
# 容器入口：统一处理 docker/podman、rootful/rootless 四种组合的 uid 映射差异。
#
# 绑定挂载 ./data 时，宿主目录属主是登录用户（如 uid 1000），而镜像内服务进程
# 若以固定 uid 1000 运行，在 rootless podman 下会映射为宿主 uid 101000，无写权限。
# 因此以 root 启动时（rootful docker 为真 root；rootless podman 的 root 映射为
# 登录用户），先把数据目录调整为 PUID/PGID 属主，再经 gosu 降权运行服务；
# 非 root 启动（如 docker --user / podman --userns=keep-id）则直接执行。
set -e

if [ "$(id -u)" = "0" ]; then
    PUID="${PUID:-1000}"
    PGID="${PGID:-1000}"
    mkdir -p /app/data
    chown -R "$PUID:$PGID" /app/data
    exec gosu "$PUID:$PGID" "$@"
fi

exec "$@"
