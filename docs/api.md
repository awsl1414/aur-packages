# API 路由文档

- **Base URL**：`http://127.0.0.1:8000`
- **版本前缀**：`/api/v1`；新增不兼容变更时引入 `/api/v2`
- **交互式文档**：`/docs`（Swagger UI）、`/redoc`

> 启动服务：`uv run main.py`

---

## 统一响应结构

所有响应（成功与错误）均使用统一包装体：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `code` | `integer` | 业务码。`0` 表示成功，非 `0` 表示错误（前三位对齐 HTTP 状态码，后两位为子码） |
| `message` | `string` | 描述信息 |
| `data` | `object \| null` | 业务数据；错误时为 `null` |

### 成功响应

```json
{
  "code": 0,
  "message": "ok",
  "data": { /* 业务数据 */ }
}
```

### 错误响应

```json
{
  "code": 40400,
  "message": "包 'xxx' 未注册",
  "data": null
}
```

HTTP 状态码与 `code` 前三位对齐（404 / 422 / 429 / 502 / 503 / 500）。

### 业务码

| 业务码 | HTTP | 触发条件 |
| --- | --- | --- |
| `0` | `200` | 成功 |
| `40400` | `404` | 包名未注册 |
| `42200` | `422` | 请求参数校验失败 |
| `42900` | `429` | 手动刷新触发 per-package 节流 |
| `50200` | `502` | refresh 时上游拉取失败或版本解析失败 |
| `50300` | `503` | 包已注册但尚无任何成功版本快照（数据未就绪） |
| `50000` | `500` | 服务内部错误 |

---

## 数据模型

### `PackageList`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `packages` | `string[]` | 已注册包名 |

### `PackageInfo`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `name` | `string` | 包名 |
| `version` | `string` | 版本号（含构建号，如 `3.2.29_260528`） |
| `urls` | `object<string, string>` | 架构 → 原始未签名下载 URL |
| `hashes` | `object<string, string\|null>` | 架构 → 文件 hash；单架构 `null` 表示计算/签名失败 |

---

## 路由

### 列出所有已注册包

```
GET /api/v1/packages
```

**请求**：无参数。

**响应** `200` — `ApiResponse<PackageList>`

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "packages": ["qq"]
  }
}
```

---

### 查询指定包的最新版本与文件 hash

```
GET /api/v1/packages/{name}
```

**请求**

路径参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `name` | `string` | 包名（如 `qq`） |

查询参数：

| 参数 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `algorithm` | `string` | `b2` | hash 算法：`b2`（BLAKE2b）/ `sha256` / `sha512` |

**数据来源（纯 DB 读 + 后台异步刷新）**：接口只读数据库，立即返回最新成功版本快照与所请求算法的各架构 hash，**永不触发网络下载**——因此响应快且不会因上游下载失败而 502。若版本快照年龄超过 `[database].version_stale_seconds`，接口会在返回后 fire-and-forget 触发一次后台采集（受节流与并发锁约束），使下次轮询拿到新鲜数据；首次查询尚无任何成功快照的包时返回 `503`（数据未就绪）。

版本采集与 hash 下载是两个独立域：版本号永远先于 hash 落库，hash 下载失败只会让对应架构的 hash 为 `null`，不会影响版本号的可用性。

**响应** `200` — `ApiResponse<PackageInfo>`（单架构 `null` 表示该架构签名/下载失败或尚未采集）

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "name": "qq",
    "version": "3.2.29_260528",
    "urls": {
      "x86_64": "https://qqdl.gtimg.cn/.../QQ_3.2.29_260528_amd64_01.deb",
      "aarch64": "https://qqdl.gtimg.cn/.../QQ_3.2.29_260528_arm64_01.deb",
      "loong64": "https://qqdl.gtimg.cn/.../QQ_3.2.29_260528_loongarch64_01.deb"
    },
    "hashes": {
      "x86_64": "8a1e...（blake2b 摘要）",
      "aarch64": "f3c2...",
      "loong64": null
    }
  }
}
```

**错误响应**

| 业务码 | HTTP | `message` |
| --- | --- | --- |
| `40400` | `404` | `包 'xxx' 未注册` |
| `42200` | `422` | `参数校验失败: <字段>: <原因>` |
| `50300` | `503` | `包 'xxx' 数据尚未就绪，请稍后重试`（尚无成功版本快照） |
| `50000` | `500` | `内部错误` |

---

### 手动触发采集并落库

```
POST /api/v1/packages/{name}/refresh
```

立即采集指定包的最新版本与文件 hash 并写入数据库，复用定时采集的同一采集 + 落库路径。
用于改完配置后立即生效、排障，或主动刷新快照。

**请求**

路径参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `name` | `string` | 包名（如 `qq`） |

**响应** `200` — `ApiResponse<PackageInfo>`（结构与 `GET /packages/{name}` 一致）

**错误响应**

| 业务码 | HTTP | `message` |
| --- | --- | --- |
| `40400` | `404` | `包 'xxx' 未注册` |
| `42900` | `429` | `包 'xxx' 采集过于频繁，请稍后重试` |
| `50200` | `502` | 版本源拉取或版本号解析失败（hash 下载失败不抛错，仅对应架构 hash 为 `null`） |
| `50000` | `500` | 调度服务未初始化（定时功能未启用时） |

---

### 重新加载包配置并同步调度

```
POST /api/v1/packages/reload
```

从数据库重新加载 `packages` 表，**即时对齐**运行时状态——重建内存注册表（`fetch_url`/`archs`/`parser_type`）与调度计划（`schedule_type`/`interval`/`cron_expr`/`enabled`）。
新增、修改、删除 `packages` 行后调用一次即可生效，无需重启。

**请求**：无参数。

**响应** `200` — `ApiResponse<PackageList>`（重载后 enabled 的包名列表）

```json
{
  "code": 0,
  "message": "ok",
  "data": { "packages": ["qq"] }
}
```

**错误响应**

| 业务码 | HTTP | `message` |
| --- | --- | --- |
| `50000` | `500` | 调度服务未初始化（定时功能未启用时） |

---

## 定时采集与数据库

- **包配置**以 SQLite 数据库 `packages` 表为唯一来源；新增包只需插入一行（`parser_type` / `fetch_url` / `archs` / `schedule_type` / `interval_seconds` / `cron_expr`），重启或调用 reload 即生效。
- **调度模式**：`interval`（按 `interval_seconds` 固定间隔）或 `cron`（标准 5 字段 `cron_expr`，按 `[scheduler].timezone` 求值）。二选一。
- **启动即采集**：`[scheduler].run_on_startup` 控制 interval 模式启动时是否立即采集一次（默认 `false`，首次采集推迟到一个间隔之后，避免每次重启都跑全量）；cron 模式始终从下一个表达式匹配时刻触发。
- **采集结果**分两域独立落库：`package_versions`（版本快照，状态 `success` / `failed`，仅反映版本抓取）与 `package_hashes`（架构 × 算法粒度，含逐架构 `status` / `error`）。两者各自独立事务，版本先行落库、永不被 hash 下载失败回滚。
- **最新版本**可通过视图 `v_latest_versions` 查询（取每个包最新 `success` 版本行，含 `urls`）；aur-packages 批量读取建议直连 SQLite 查该视图，无需走 HTTP。
- `GET /packages/{name}` 为**纯 DB 读**：只返回快照、不下载；版本过期时后台异步刷新，不影响响应。
