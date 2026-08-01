-- AUR Packages Helper —— 定时采集结果库 schema（SQLite）
--
-- 业务定位：定时任务按 packages 配置抓取各包版本、计算文件 hash，
-- 落库后供 aur-packages 更新 PKGBUILD 时查询。三张表 + 一个取「最新版本」的视图。
--
-- 与 ORM 的关系：Tortoise ORM 模型字段须与本文件保持一致；本文件作为
-- 数据库结构的事实来源（source of truth），便于直接初始化或迁移比对。
-- 启用外键约束须在连接时执行 `PRAGMA foreign_keys = ON;`（SQLite 默认关闭）。
--
-- 时间列统一用 TEXT（ISO8601，如 2026-08-01T12:00:00Z），与 Tortoise 的
-- DatetimeField(auto_now_add=True) 默认输出一致，便于排序与跨时区处理。
--
-- 字段含义以行内 ``-- ...`` 注释标注。SQLite 不支持 ``COMMENT ON COLUMN``，
-- 但会把 CREATE 语句原样存入 sqlite_master，故在 DB 内用 ``.schema <table>``
-- 或 ``SELECT sql FROM sqlite_master WHERE name='<table>'`` 即可看到字段注释。

PRAGMA foreign_keys = ON;

-- ─────────────────────────────────────────────────────────────────────────────
-- 包采集配置
-- 与 app/registry.py 的 PackageEntry 对应；定时调度从本表读取工作集，
-- 将包定义从代码硬编码迁移到可配置、可持久化。
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS packages (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,        -- 主键，自增
    name             TEXT    NOT NULL UNIQUE,                   -- 包名，如 qq
    parser_type      TEXT    NOT NULL,                          -- 解析器类型，对应 app/parsers/*，如 qq
    fetch_url        TEXT    NOT NULL,                          -- 版本信息源 URL
    archs            TEXT    NOT NULL,                          -- 支持架构，JSON 数组，如 ["x86_64","aarch64"]
    parser_config    TEXT,                                      -- parser 构造参数 JSON（可空），如 {"region":"sg"} / {"urls":{"x86_64":"..."}}
    hash_algorithm   TEXT    NOT NULL DEFAULT 'b2',             -- 定时采集使用的 hash 算法：b2 / sha256 / sha512
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
-- 种子数据：QQ 包（interval 模式，每小时采集一次）
-- ON CONFLICT 保证重复执行 schema.sql 不插重复行
-- ─────────────────────────────────────────────────────────────────────────────
INSERT INTO packages (name, parser_type, fetch_url, archs, schedule_type, interval_seconds)
VALUES (
    'qq', 'qq',
    'https://qq-web.cdn-go.cn/im.qq.com_new/latest/rainbow/pcConfig.json',
    '["x86_64","aarch64","loong64"]',
    'interval', 14400
)
ON CONFLICT(name) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- 种子数据：其余包（interval 模式，每小时采集一次；hash_algorithm 走默认 b2）
-- parser_config 提供 parser 构造参数；无参 parser 留空
-- ─────────────────────────────────────────────────────────────────────────────

-- Navicat：版本取自 release-note HTML，下载 URL 为固定 AppImage 直链，经 parser_config.urls 注入
INSERT INTO packages (name, parser_type, fetch_url, archs, parser_config, schedule_type, interval_seconds)
VALUES (
    'navicat', 'navicat',
    'https://www.navicat.com.cn/products/navicat-premium-release-note#L',
    '["x86_64","aarch64"]',
    '{"urls":{"x86_64":"https://dn.navicat.com/download/navicat17-premium-cs-x86_64.AppImage","aarch64":"https://dn.navicat.com/download/navicat17-premium-cs-aarch64.AppImage"}}',
    'interval', 14400
)
ON CONFLICT(name) DO NOTHING;

-- bt-dualboot-ng：PyPI sdist（纯 Python，arch=any）
INSERT INTO packages (name, parser_type, fetch_url, archs, schedule_type, interval_seconds)
VALUES (
    'bt-dualboot-ng', 'pypi',
    'https://pypi.org/pypi/bt-dualboot-ng/json',
    '["any"]',
    'interval', 14400
)
ON CONFLICT(name) DO NOTHING;

-- Trae 国际版：同一 API，按 region 选不同机房 CDN（cn / sg / va）
INSERT INTO packages (name, parser_type, fetch_url, archs, parser_config, schedule_type, interval_seconds)
VALUES (
    'trae', 'trae',
    'https://icube-normal.trae.ai/icube/api/v1/native/version/trae/latest',
    '["x86_64","aarch64"]',
    '{"region":"cn"}',
    'interval', 14400
)
ON CONFLICT(name) DO NOTHING;

INSERT INTO packages (name, parser_type, fetch_url, archs, parser_config, schedule_type, interval_seconds)
VALUES (
    'trae-sg', 'trae',
    'https://icube-normal.trae.ai/icube/api/v1/native/version/trae/latest',
    '["x86_64","aarch64"]',
    '{"region":"sg"}',
    'interval', 14400
)
ON CONFLICT(name) DO NOTHING;

-- trae-us 用 region=va（弗吉尼亚机房，上游 download[] 直传该值，非 us→va 映射）
INSERT INTO packages (name, parser_type, fetch_url, archs, parser_config, schedule_type, interval_seconds)
VALUES (
    'trae-us', 'trae',
    'https://icube-normal.trae.ai/icube/api/v1/native/version/trae/latest',
    '["x86_64","aarch64"]',
    '{"region":"va"}',
    'interval', 14400
)
ON CONFLICT(name) DO NOTHING;

-- Trae 国内版：独立 API（api.trae.cn），与国际版是不同产品
INSERT INTO packages (name, parser_type, fetch_url, archs, parser_config, schedule_type, interval_seconds)
VALUES (
    'trae-cn', 'trae',
    'https://api.trae.cn/icube/api/v1/native/version/trae/cn/latest',
    '["x86_64","aarch64"]',
    '{"region":"cn"}',
    'interval', 14400
)
ON CONFLICT(name) DO NOTHING;

-- Zen Browser 每夜版：GitHub Releases 固定标签 twilight-1
INSERT INTO packages (name, parser_type, fetch_url, archs, schedule_type, interval_seconds)
VALUES (
    'zen-browser', 'zen',
    'https://api.github.com/repos/zen-browser/desktop/releases/tags/twilight-1',
    '["x86_64","aarch64"]',
    'interval', 14400
)
ON CONFLICT(name) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- 版本快照：定时任务每次采集产出一条
-- 保留全部历史，便于版本变更检测与故障审计；最新版本通过视图查询。
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS package_versions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    package_id  INTEGER NOT NULL,                                -- 所属包，关联 packages.id（ON DELETE CASCADE）
    version     TEXT,                                            -- 解析到的版本号；采集失败时可为 NULL
    status      TEXT    NOT NULL CHECK (status IN ('success', 'partial', 'failed')), -- success=全量成功；partial=部分架构失败；failed=整包失败
    error       TEXT,                                            -- failed 时记录失败原因
    fetched_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),   -- 采集时间
    FOREIGN KEY (package_id) REFERENCES packages (id) ON DELETE CASCADE
) STRICT;

-- 取某包最新快照的核心索引：按包倒序取时间
CREATE INDEX IF NOT EXISTS idx_versions_package_time ON package_versions (package_id, fetched_at DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- 文件 hash：版本快照下「架构 × 算法」粒度的记录
-- 对齐 app/constants/package.py 的 ArchEnum（x86_64/aarch64/loong64/...）
-- 与 HashAlgorithmEnum（sha256/sha512/b2）。
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS package_hashes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    version_id  INTEGER NOT NULL,                                -- 所属版本快照，关联 package_versions.id（ON DELETE CASCADE）
    arch        TEXT    NOT NULL,                                -- CPU 架构，如 x86_64
    algorithm   TEXT    NOT NULL,                                -- 哈希算法，如 b2
    hash_value  TEXT,                                            -- 计算结果；NULL 表示该架构采集失败
    url         TEXT,                                            -- 原始下载 URL（parse_url 结果，稳定不过期；不存签名后的临时链接）
    fetched_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),  -- 该条 hash 的采集时间（UTC，ISO8601）
    FOREIGN KEY (version_id) REFERENCES package_versions (id) ON DELETE CASCADE,
    -- 同一版本下同一架构同一算法只保留一条，保证插入幂等
    UNIQUE (version_id, arch, algorithm)
) STRICT;

-- 按架构 + 算法检索（如查询某架构最新 b2）
CREATE INDEX IF NOT EXISTS idx_hashes_arch_algo ON package_hashes (arch, algorithm);

-- ─────────────────────────────────────────────────────────────────────────────
-- 视图：每个包的最新版本快照，供 aur-packages 直接读取
-- 取 fetched_at 最大者；同时间取 id 最大者保证确定性与唯一。
-- ─────────────────────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS v_latest_versions;
CREATE VIEW v_latest_versions AS
SELECT
    p.id           AS package_id,   -- 包 id（packages.id）
    p.name,                        -- 包名
    p.enabled,                     -- 是否启用定时采集
    v.id           AS version_id,  -- 最新版本快照 id（无快照时为 NULL）
    v.version,                     -- 版本号（采集失败时为 NULL）
    v.status,                      -- success / partial / failed
    v.error,                       -- failed 时的失败原因
    v.fetched_at                   -- 最新快照采集时间（UTC，ISO8601）
FROM packages p
LEFT JOIN package_versions v ON v.id = (
    SELECT vv.id
    FROM package_versions vv
    WHERE vv.package_id = p.id
    ORDER BY vv.fetched_at DESC, vv.id DESC
    LIMIT 1
);
