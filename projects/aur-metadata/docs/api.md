# API 路由文档

- **Base URL**：`http://127.0.0.1:8000`
- **版本前缀**：`/api/v1`；新增不兼容变更时引入 `/api/v2`
- **交互式文档**：`/docs`（Swagger UI）、`/redoc`

> 启动服务：`uv run aur-metadata`（本成员目录内执行）

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
| `urls` | `object<string, string>` | 架构 → 原始未签名下载 URL（写入 PKGBUILD 的稳定链接） |
| `download_urls` | `object<string, string\|null>` | 架构 → 查询时实时生成的可直接下载 URL（QQ 为临时签名链接，会过期）；`null` 表示该架构签名失败；空 dict 表示本响应未提供实时链接（如 refresh 路径），消费方应回退 `urls` 或自行完成鉴权 |


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

### 查询指定包的最新版本与下载 URL

```
GET /api/v1/packages/{name}
```

**请求**

路径参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `name` | `string` | 包名（如 `qq`） |

**数据来源（DB 读 + 实时签名）**：接口只读数据库返回最新成功版本快照，**不触发采集、不下载安装包体**。仅鉴权类源（QQ）会在查询时发起轻量签名 RPC 生成 `download_urls`，单架构失败置 `null` 降级、不影响响应。首次查询尚无任何成功快照的包时返回 `503`（数据未就绪），需等定时采集或手动 `refresh`。

快照的新鲜度只由每包的定时采集保证；本服务不计算校验和，消费方下载安装包后本地计算。

**响应** `200` — `ApiResponse<PackageInfo>`（`download_urls` 中单架构 `null` 表示该架构签名失败）

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
    "download_urls": {
      "x86_64": "https://qqdl.gtimg.cn/.../QQ_3.2.29_260528_amd64_01.deb?sign=...",
      "aarch64": "https://qqdl.gtimg.cn/.../QQ_3.2.29_260528_arm64_01.deb?sign=...",
      "loong64": null
    }
  }
}
```

**错误响应**

| 业务码 | HTTP | `message` |
| --- | --- | --- |
| `40400` | `404` | `包 'xxx' 未注册` |
| `50300` | `503` | `包 'xxx' 数据尚未就绪，请稍后重试`（尚无成功版本快照） |
| `50000` | `500` | `内部错误` |

---

### 手动触发采集并落库

```
POST /api/v1/packages/{name}/refresh
```

立即采集指定包的最新版本与下载 URL 并写入数据库，复用定时采集的同一路径。
只抓版本源/安装包头部，不下载完整安装包、不计算校验和。用于改完配置后立即生效、
排障，或主动刷新快照。**不依赖调度器启用**（采集与调度解耦）。

**请求**

路径参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `name` | `string` | 包名（如 `qq`） |

**响应** `200` — `ApiResponse<PackageInfo>`（结构与 `GET /packages/{name}` 一致，但 `download_urls` 恒为空 dict——采集路径不做实时签名，消费方回退 `urls`）

**错误响应**

| 业务码 | HTTP | `message` |
| --- | --- | --- |
| `40400` | `404` | `包 'xxx' 未注册` |
| `42900` | `429` | `包 'xxx' 采集过于频繁，请稍后重试` |
| `50200` | `502` | 版本源拉取或版本号解析失败 |

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
- **启动即采集**：`[scheduler].run_on_startup` 控制 interval 模式启动时是否立即采集一次（默认开启：重启后立即补一轮，避免停机期间的版本变化要等满一个间隔才可见；设为 `false` 则首次采集推迟一个间隔）；cron 模式始终从下一个表达式匹配时刻触发。
- **执行模型**：每包一个独立 task（`max_running_jobs=1`），互不排队；迟到任务不丢弃（`misfire_grace_time=None`），积压由 coalesce 与并发上限收敛。
- **采集结果**落 `package_versions`（状态 `success` / `failed`）。版本未变时复用现有 success 行，只刷新 `urls` 与 `fetched_at`；版本变化或失败才新增行。
- **最新版本**可通过视图 `v_latest_versions` 查询（取每个包最新 `success` 版本行，含 `urls`）；aur-packages 批量读取建议直连 SQLite 查该视图，无需走 HTTP。
- `GET /packages/{name}` 只读快照（鉴权类源仅实时签名 RPC 生成 `download_urls`），不触发采集；新鲜度由每包定时任务保证。
