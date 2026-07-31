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

HTTP 状态码与 `code` 前三位对齐（404 / 422 / 502 / 500）。

### 业务码

| 业务码 | HTTP | 触发条件 |
| --- | --- | --- |
| `0` | `200` | 成功 |
| `40400` | `404` | 包名未注册 |
| `42200` | `422` | 请求参数校验失败 |
| `42900` | `429` | 采集过于频繁（触发 per-package 节流） |
| `50200` | `502` | 上游数据源拉取失败或版本解析失败 |
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

**数据来源（DB 优先 + TTL 回源）**：接口优先返回数据库内最新且在 `[http].hash_cache_ttl_seconds` 有效期内的采集快照；快照过期、缺失、最新快照为 `failed`、或所请求算法无对应 hash 记录时，才回源实时下载计算（较慢）。回源结果不落库——落库由定时任务与 `POST /refresh` 负责。

**响应** `200` — `ApiResponse<PackageInfo>`（`hashes` 总填充；单架构 `null` 表示该架构签名/下载失败）

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
| `42900` | `429` | `包 'xxx' 采集过于频繁，请稍后重试`（缓存未命中且触发节流时） |
| `50200` | `502` | `无法获取 xxx 的版本信息` 等 |
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
| `50200` | `502` | 上游拉取/解析/下载失败 |
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
- **采集结果**落 `package_versions`（每次一条版本快照，状态 `success` / `partial` / `failed`）与 `package_hashes`（架构 × 算法粒度）。
- **最新版本**可通过视图 `v_latest_versions` 查询；aur-packages 批量读取建议直连 SQLite 查该视图，无需走 HTTP。
- `GET /packages/{name}` 采用 **DB 优先 + TTL 回源**策略：优先返回数据库新鲜快照，过期或缺失时才实时计算。
