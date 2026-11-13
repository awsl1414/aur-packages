-- aur-metadata —— 定时采集结果库 schema（SQLite）
--
-- 业务定位：定时任务按 packages 配置抓取各包版本与下载 URL，
-- 落库后供 aur-packages 更新 PKGBUILD 时查询。两张表 + 一个取「最新版本」的视图。
-- 校验和不在本库计算：消费方下载安装包后本地计算。
--
-- 与 ORM 的关系：Tortoise ORM 模型字段须与本文件保持一致；本文件作为
-- 数据库结构的事实来源（source of truth），便于直接初始化或迁移比对。
-- 启用外键约束须在连接时执行 `PRAGMA foreign_keys = ON;`（SQLite 默认关闭）。
--
-- 时间列统一用 TEXT（ISO8601，如 2026-08-01T12:00:00Z）：ORM 写入即此格式，
-- DEFAULT 仅兜底裸 SQL 插入；统一格式保证字符串排序与跨时区语义正确。
--
-- 字段含义以行内 ``-- ...`` 注释标注。SQLite 不支持 ``COMMENT ON COLUMN``，
-- 但会把 CREATE 语句原样存入 sqlite_master，故在 DB 内用 ``.schema <table>``
-- 或 ``SELECT sql FROM sqlite_master WHERE name='<table>'`` 即可看到字段注释。

PRAGMA foreign_keys = ON;

-- ─────────────────────────────────────────────────────────────────────────────
-- 包采集配置
-- 与 src/aur_metadata/registry.py 的 PackageEntry 对应；定时调度从本表读取工作集。
-- 包定义的来源是项目根 packages.toml：启动时由 package_seeder 按 name
-- upsert 到本表，本文件不含种子数据。
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS packages (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,        -- 主键，自增
    name             TEXT    NOT NULL UNIQUE,                   -- 包名，如 qq
    parser_type      TEXT    NOT NULL,                          -- 解析器类型，对应 src/aur_metadata/parsers/*，如 qq
    fetch_url        TEXT    NOT NULL,                          -- 版本信息源 URL
    archs            TEXT    NOT NULL,                          -- 支持架构，JSON 数组，如 ["x86_64","aarch64"]
    parser_config    TEXT,                                      -- parser 构造参数 JSON（可空），如 {"region":"sg"} / {"urls":{"x86_64":"..."}}
    enabled          INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),     -- 是否纳入定时采集
    schedule_type    TEXT    NOT NULL DEFAULT 'interval' CHECK (schedule_type IN ('interval', 'cron')), -- 调度模式
    interval_seconds INTEGER CHECK (interval_seconds IS NULL OR interval_seconds > 0), -- interval 模式下的采集间隔（秒）
    cron_expr        TEXT,                                      -- cron 模式下的标准 5 字段表达式，如 "30 3 * * *"
    description      TEXT,                                      -- 包说明（运维备注，可选）
    created_at       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),  -- 记录创建时间（UTC，ISO8601）
    updated_at       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),  -- 记录最近更新时间（UTC，ISO8601；由 ORM auto_now 维护）
    -- enabled=0 不校验调度参数；启用时 interval 与 cron 二选一必填
    CHECK (
        enabled = 0
        OR (schedule_type = 'interval' AND interval_seconds IS NOT NULL AND interval_seconds > 0)
        OR (schedule_type = 'cron' AND cron_expr IS NOT NULL AND length(cron_expr) > 0)
    )
) STRICT;

-- 按启用状态筛选工作集
CREATE INDEX IF NOT EXISTS idx_packages_enabled ON packages (enabled);

-- ─────────────────────────────────────────────────────────────────────────────
-- 版本快照：版本变化或采集失败时新增一行。
-- 版本未变时复用现有 success 行（只刷新 urls 与 fetched_at），不新增历史。校验和由消费方（aur-auto-update）下载后本地计算，
-- 本表不存储 hash。
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS package_versions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    package_id  INTEGER NOT NULL,                                -- 所属包，关联 packages.id（ON DELETE CASCADE）
    version     TEXT,                                            -- 解析到的版本号；版本抓取失败时为 NULL
    urls        TEXT,                                            -- 各架构原始下载 URL JSON（arch→url），成功时写入
    status      TEXT    NOT NULL CHECK (status IN ('success', 'failed')), -- 仅反映版本抓取结果
    error       TEXT,                                            -- failed 时记录失败原因
    fetched_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),   -- 采集时间
    FOREIGN KEY (package_id) REFERENCES packages (id) ON DELETE CASCADE
) STRICT;

-- 取某包最新快照的核心索引：按包倒序取时间
CREATE INDEX IF NOT EXISTS idx_versions_package_time ON package_versions (package_id, fetched_at DESC);


-- ─────────────────────────────────────────────────────────────────────────────
-- 视图：每个包的最新「成功」版本快照，供 aur-packages 直接读取
-- 仅取 status='success' 的最新行（version 可信）；failed 审计行不参与。
-- 同时间取 id 最大者保证确定性与唯一。
-- ─────────────────────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS v_latest_versions;
CREATE VIEW v_latest_versions AS
SELECT
    p.id           AS package_id,   -- 包 id（packages.id）
    p.name,                        -- 包名
    p.enabled,                     -- 是否启用定时采集
    v.id           AS version_id,  -- 最新成功版本快照 id（无成功快照时为 NULL）
    v.version,                     -- 版本号
    v.urls,                        -- 各架构原始下载 URL JSON
    v.fetched_at                   -- 最新成功快照采集时间（UTC，ISO8601）
FROM packages p
LEFT JOIN package_versions v ON v.id = (
    SELECT vv.id
    FROM package_versions vv
    WHERE vv.package_id = p.id AND vv.status = 'success'
    ORDER BY vv.fetched_at DESC, vv.id DESC
    LIMIT 1
);
