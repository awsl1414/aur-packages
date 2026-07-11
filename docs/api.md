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
| `hashes` | `object<string, string\|null> \| null` | 架构 → 文件 hash；`null` 表示未请求，单架构 `null` 表示计算失败 |

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

### 查询指定包的最新版本与可选信息

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
| `with_hash` | `boolean` | `false` | 是否计算文件 hash。为 `true` 时流式下载各架构文件并计算摘要，**响应较慢** |
| `algorithm` | `string` | `b2` | hash 算法：`b2`（BLAKE2b）/ `sha256` / `sha512`。仅在 `with_hash=true` 时生效 |

**响应** `200` — `ApiResponse<PackageInfo>`

默认（`with_hash=false`）：

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
    "hashes": null
  }
}
```

`with_hash=true` 时 `hashes` 填充（单架构 `null` 表示该架构签名或下载失败，不影响其它架构）：

```json
{
  "hashes": {
    "x86_64": "8a1e...（blake2b 摘要）",
    "aarch64": "f3c2...",
    "loong64": null
  }
}
```

**错误响应**

| 业务码 | HTTP | `message` |
| --- | --- | --- |
| `40400` | `404` | `包 'xxx' 未注册` |
| `42200` | `422` | `参数校验失败: <字段>: <原因>` |
| `50200` | `502` | `无法获取 xxx 的版本信息` 等 |
| `50000` | `500` | `内部错误` |
