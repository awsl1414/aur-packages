# Graph Report - aur-packages  (2026-09-20)

## Corpus Check
- 128 files · ~35,816 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 46 file(s) not represented in the graph (top: (none) 29, .install 7, .desktop 5)

## Summary
- 1507 nodes · 2890 edges · 159 communities (88 shown, 71 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 311 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `233f1c5b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_package_seeder.py
- .__exit__
- AppImage Dependency Analysis Practice
- test_schedule_service.py
- test_package_service.py
- Path
- Rationale: zen-browser-twilight-bin uses b2sums but updater hardcoded SHA512
- aur_metadata/constants/__init__.py
- AUR 打包实践指南
- PackageUpdater
- ApiParser
- TraeParser
- test_package_service_deb.py
- AUR 包自动更新工具
- packages.py
- 设计
- parsers/registry.py
- ArchEnum
- Fetcher
- AppImage 解包
- Electron 直装（tarball）
- 类型注解规范
- CONTRIBUTORS List
- deb 解包
- DLAGENTS 自定义下载代理 [推荐实践]
- aur-auto-update
- linuxqq-nt Package
- 源码编译
- post-commit
- linuxqq-get-url.sh
- structure/
- 版本 [官方规范]
- 依赖 [官方规范]
- post-checkout
- linuxqq.sh
- navicat17-premium-zh-cn
- trae-sg
- trae-us
- Keep Repository Alive Workflow
- PKGBUILDEditor
- zen-browser-twilight.sh
- test_base_parser.py
- navicat.sh
- trae-cn.sh
- NavicatParser
- CLAUDE.md Project Instructions
- linuxqq-nt package (Electron QQ)
- AUR 包已知问题
- Update Packages Workflow
- trae-sg/trae.sh
- trae/trae.sh
- trae-us/trae.sh
- trae
- config.py
- .githooks/commit-msg
- CONTRIBUTING Guide
- README - AUR Package Auto-Updater
- Dev-Main Branch Strategy
- linuxqq-nt
- CONTRIBUTORS.md
- BaseParser Plugin Pattern
- zen-browser-twilight-bin
- test_api_packages.py
- Package
- extract_extension_from_url
- navicat17-premium-zh-cn Package
- trae Package (China CDN)
- trae-cn Package (Domestic)
- trae-sg Package (Singapore CDN)
- trae-us Package (US CDN)
- No ${CARCH} in source_<arch> Rule
- Electron SUID Sandbox Practice
- Launcher Script Path Coupling Risk
- Local Source Hash Sync Rule
- pkgrel Revision Rule
- pkgver Versioning Rule
- Rolling Release Source Checksum Rule
- Source Alias Cache-Busting Rule
- Virtual Package (provides) Practice
- PackageService
- test_response.py
- test_pypi_parser.py
- .fetch_and_hash_multi
- aur-metadata
- test_qq_parser.py
- .load_from_yaml
- compare_versions
- DebParseError
- test_fetcher_retry.py
- test_zen_parser.py
- package_service.py
- load_packages
- PackageConfig
- blake2b hash builder registration (_HASH_BUILDERS)
- get_effective_hash_algorithm method
- hash_algorithm config field (Settings + PackageConfig override)
- PackageUpdater hardcoded SHA512 elimination
- PKGBUILDEditor hash_algorithm parameterization
- B2 unit tests (hash + pkgbuild_editor)
- aria2c Multi-threaded Downloader
- makepkg Build Tool
- namcap PKGBUILD Linter
- test_fetcher_head.py
- uv Package Manager
- PackageVersion
- models/__init__.py
- package_updater.py
- QQParser
- navicat17-premium-zh-cn package (Chinese Simplified)
- Trae AI IDE by ByteDance (CDN variants)
- zen-browser-twilight-bin package (Firefox-based nightly)
- aur_metadata/utils/hash.py
- ._update_scalar_field
- PackageInfo
- response.py
- calculate_file_hash
- HashAlgorithmEnum (SHA256/SHA512/B2)
- DebParser
- PackageEntry
- test_deb_parser.py
- ApiResponse
- config_loader.py
- _make_downloader
- fakes.py
- ._update_source_field
- Downloader
- TestPKGBUILDEditorEpoch
- normalize_deb_version
- ._json_section
- 注释规范
- PyPIParser
- ZenParser
- aur-metadata/AGENTS.md
- test_parse_url_unknown_arch_warns_and_none
- test_parse_url_region_selection
- test_version_from_package_head_bad_structure
- aur-metadata/.githooks/commit-msg
- aur-metadata
- aur-packages

## God Nodes (most connected - your core abstractions)
1. `ArchEnum` - 73 edges
2. `PKGBUILDEditor` - 73 edges
3. `PackageService` - 46 edges
4. `BaseParser` - 37 edges
5. `PackageUpdater` - 30 edges
6. `make_app_config()` - 29 edges
7. `AppConfig` - 28 edges
8. `TraeParser` - 27 edges
9. `ApiParser` - 26 edges
10. `FakeScheduler` - 25 edges

## Surprising Connections (you probably didn't know these)
- `添加新软件包` --references--> `pkgbuild()`  [INFERRED]
  AGENTS.md → projects/aur-auto-update/tests/updater/test_pkgbuild_editor.py
- ``PackageInfo`` --references--> `PackageInfo`  [INFERRED]
  projects/aur-metadata/docs/api.md → projects/aur-metadata/src/aur_metadata/schemas.py
- `使用` --references--> `pkgbuild()`  [INFERRED]
  projects/aur-auto-update/README.md → projects/aur-auto-update/tests/updater/test_pkgbuild_editor.py
- `定时采集与数据库` --references--> `success()`  [INFERRED]
  projects/aur-metadata/docs/api.md → projects/aur-metadata/src/aur_metadata/response.py
- ``PackageList`` --references--> `PackageList`  [INFERRED]
  projects/aur-metadata/docs/api.md → projects/aur-metadata/src/aur_metadata/schemas.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **B2 hash support implementation flow (Enum → Config → Updater)** — specs_hash_algorithm_enum, specs_blake2b_builder, specs_hash_algorithm_field, specs_pkgbuild_editor_api, specs_package_updater_hardcode_removal [EXTRACTED 0.95]
- **Update → SRCINFO → Commit → AUR Push Pipeline** — github_workflows_update_packages, wf_arch_pkg_action, wf_aur_deploy_action, rules_srcinfo [INFERRED 0.85]
- **makepkg checksum / cache-busting rule cluster** — rules_source_alias_cache, rules_carch_in_source, rules_local_source_hash, rules_rolling_release_checksum, tool_makepkg [INFERRED 0.85]

## Communities (159 total, 71 thin omitted)

### Community 0 - "test_package_seeder.py"
Cohesion: 0.06
Nodes (57): importlib, create_app(), lifespan(), FastAPI, 应用生命周期：初始化 DB、同步包配置、加载注册表、启停调度器 包配置以 DB 为运行时唯一来源——启动时先执行 schema.sql 建库， 再把…, 构造 FastAPI 应用 Args: config: 应用运行配置（configs/config.toml 加载） packages:…, PackageConfig, 单个包的采集配置（packages.toml 的 ``[[packages]]`` 项）。 本类只做结构层校验（字段齐全、类型正确、调度二选一）；涉及运行时… (+49 more)

### Community 3 - "test_schedule_service.py"
Cohesion: 0.10
Nodes (38): apscheduler_triggers_interval, _build_service(), _cfg(), FakeScheduler, _pkg(), Any, aur_metadata.services.schedule_service 测试。 覆盖：trigger 构造、schedule…, fire_now=False 时首次推迟一个间隔，避免 reload/重启立即全量采集 (+30 more)

### Community 4 - "test_package_service.py"
Cohesion: 0.08
Nodes (36): Event, FakeFetcher, make_qq_registry(), 桩：某架构在 ``_hashes`` 有值视为下载成功，全部算法均返回该 digest；缺失则 None。, 伪装成 Fetcher 供 PackageService 使用（ty 兼容）。, 构造单包 'qq' 的 registry：archs 决定可解析架构，每架构 URL 自动派生。 抽出共享构造，避免 package_service /…, 可控 Fetcher：fetch_text 返回预设文本，fetch_and_hash_many 返回预设 hash。 - ``text=None``…, aur_metadata.services.package_service 集成测试（DB + Fake 桩）。 覆盖解耦后的新契约： - 节流 /… (+28 more)

### Community 5 - "Path"
Cohesion: 0.09
Nodes (19): Path, 更新 source URL 时保留 :: 别名, update_source（arch 特定）替换逻辑的边界条件测试, URL 含 ${_gh}（花括号）时保留 shell 变量，不更新, URL 含 $_gh（无花括号）时同样应保留，等价于 ${_gh}, 别名含 ${pkgver}、URL 硬编码时，保留别名、替换 URL, 单行多条目：替换远程 URL，保留本地源文件, 缺失 source_<arch> 字段时不破坏其它内容 (+11 more)

### Community 7 - "aur_metadata/constants/__init__.py"
Cohesion: 0.13
Nodes (21): apscheduler_triggers_cron, dataclasses, httpx, json, logging, HTTP 客户端模块 处理 ``aur-metadata`` API 的响应语义： - 成功：HTTP 200，body…, metadata API 统一响应解析器（唯一解析器） 数据源：``aur-metadata`` 项目的 ``GET…, ApiParser 单元测试 数据源：``aur-metadata`` 的 ``GET /api/v1/packages/{name}`` 接口。 响应格式见… (+13 more)

### Community 8 - "AUR 打包实践指南"
Cohesion: 0.13
Nodes (15): AUR 打包实践指南, license [官方规范], pkgdesc [官方规范], provides 和 conflicts [推荐实践], Shell 补全 [推荐实践], source 声明 [推荐实践], .SRCINFO [官方规范], 代码质量 [推荐实践] (+7 more)

### Community 9 - "PackageUpdater"
Cohesion: 0.10
Nodes (17): PackageUpdater, Path, 从 ``parsed.hashes`` 中挑选出支持架构的校验和。 返回 ``{arch_value:…, 获取各架构校验和：优先用 metadata API 提供的 hashes，否则下载计算。 metadata 通过 ``data.hashes``…, 下载文件并计算校验和（回退路径） 使用 Downloader 的并发下载功能，并行下载单个包的所有架构, 包更新器，整合fetch、parse和update流程, 处理版本不更新的情况（当前版本 >= 新版本） 复用 update_package 已创建的 editor，避免重复加载 PKGBUILD。 两种场景： 1.…, 处理版本更新流程（new_version > current_version）。 步骤： 1. 获取 checksums：API 优先提供，否则按 urls… (+9 more)

### Community 10 - "ApiParser"
Cohesion: 0.09
Nodes (17): ApiParser, Any, metadata API 统一响应解析器。 一次 ``parse`` 返回完整的 ``ParsedPackage``，避免版本/URL/hash 分别解析时…, 解析 metadata API 响应为 ``ParsedPackage``；结构不符返回 None。, 解析 JSON 响应并返回 ``data`` 段；结构不符返回 None。, data 中无 hashes 字段时 hashes 为空字典（调用方回退下载），不算解析失败, hashes 为空字典时正常返回，hashes 为空, hash 值为 None（metadata schema 允许）时跳过该架构 (+9 more)

### Community 11 - "TraeParser"
Cohesion: 0.10
Nodes (29): Any, Trae IDE 版本解析器：JSON manifest 提取版本号与按 region 选链, 从 region 项各架构链接提取版本号并校验一致。 只扫 ``_ARCH_KEY_MAP`` 的架构链接 key（而非 entry 全部值，防未来…, 返回 ``download[]`` 中 ``region`` 匹配项；非列表或无匹配返回 None, TraeParser, _entry(), _payload(), Any (+21 more)

### Community 12 - "test_package_service_deb.py"
Cohesion: 0.12
Nodes (29): DebControlVersionMixin, deb 头部版本提取 mixin：head 字节 → control Version → 归一化版本号, _deb_service(), _DynamicDebParser, _make_deb_package(), Any, PackageService 安装包路径版本域集成测试（DebParser + Fake 桩）。 覆盖 collect_version 的…, 头部下载失败 → failed 审计行 + RuntimeError (+21 more)

### Community 13 - "AUR 包自动更新工具"
Cohesion: 0.06
Nodes (25): Commit 规范, graphify, 开发命令, 注意事项, 添加新软件包, 项目结构（uv workspace monorepo）, Commit 规范, 分支策略 (+17 more)

### Community 14 - "packages.py"
Cohesion: 0.10
Nodes (19): CronTrigger, fastapi, IntervalTrigger, get_package_service(), get_schedule_service(), FastAPI 依赖：共享服务（如 PackageService）的请求级访问入口, 从 app.state 获取 PackageService（由 lifespan 注入）。 作为 FastAPI 依赖，在端点参数中通过…, 从 app.state 获取 ScheduleService（由 lifespan 注入）。… (+11 more)

### Community 15 - "设计"
Cohesion: 0.15
Nodes (12): 1. HashAlgorithmEnum 新增 B2, 2. 注册 blake2b 构建器, 3. 配置模型新增 hash_algorithm 字段, 4. config.yaml 配置, 5. PKGBUILDEditor API 清理, 6. PackageUpdater 消除硬编码, 7. 单元测试补充, B2 (BLAKE2b) 哈希算法支持设计 (+4 more)

### Community 16 - "parsers/registry.py"
Cohesion: 0.10
Nodes (23): Navicat Premium 版本解析器 版本号从 Navicat 官网 release-note HTML 页面正则提取；下载 URL 不在页面响应里，…, get_parser(), Any, 解析器类型注册表：parser_type 字符串 → BaseParser 实例的工厂。 新增 parser 时在此注册即可，调度器/注册表加载器通过…, 按 parser_type 取一个新的解析器实例；未知类型抛 ValueError。 ``app_config``…, register_parser(), Trae IDE 版本解析器 解析 ``data.manifest.linux``：``download[]`` 中按 ``region`` 匹配项取各架构…, aur_metadata.parsers.registry 单元测试 (+15 more)

### Community 17 - "ArchEnum"
Cohesion: 0.11
Nodes (16): ABC, ArchEnum, BaseParser, 从响应数据中提取原始下载 URL（写入 PKGBUILD 的 ``source_<arch>=()``）。 返回值必须是未经签名/鉴权处理的原始…, 将 ``parse_url`` 产出的原始 URL 转为可直接下载的 URL（程序内部使用）。 默认原样返回；子类可重写以附加鉴权/签名处理，例如 QQ 对…, 返回抓取本 parser 数据源时使用的完整请求头。 设计契约：**完整替换** ``Fetcher.DEFAULT_HEADERS``，不与任何默认头…, 解析器抽象基类，定义版本号和 URL 解析接口。 子类需要实现的契约： - ``parse_version``：从 API/页面响应中提取语义化版本号 -…, 将 ArchEnum 或 str 统一为架构字符串值 (+8 more)

### Community 18 - "Fetcher"
Cohesion: 0.11
Nodes (23): Fetcher, 从 metadata 错误响应 body 中提取 ``message`` 字段。 非 JSON、非对象或缺字段时返回 None，由调用方回退到 HTTP…, HTTP 客户端封装，按 metadata API 状态码语义处理请求与重试, 获取文本数据。 - HTTP 200 → 返回 body 文本 - 4xx 永久错误 → 记日志，返回 None（不重试） - 429/5xx 或网络异常 →…, 默认开启 SSL 证书校验（verify=True 传入 httpx 客户端）, 构造一个真实 httpx.Response，便于 status_code/reason_phrase/text 都可用, verify_ssl=False 时禁用证书校验（verify=False 传入 httpx 客户端）, 404（包未注册）属永久错误，立即返回 None 且不重试 (+15 more)

### Community 19 - "AppImage 解包"
Cohesion: 0.33
Nodes (6): AppImage 依赖分析 [推荐实践], AppImage 解包, AppRun 启动问题 [推荐实践], 捆绑库冲突与 LD_PRELOAD [推荐实践], 清理冗余文件 [推荐实践], 解包流程 [推荐实践]

### Community 20 - "Electron 直装（tarball）"
Cohesion: 0.33
Nodes (6): Electron 直装（tarball）, source 文件排除 [项目约定], SUID sandbox [项目约定], 启动脚本 [项目约定], 完整示例, 构建选项 [项目约定]

### Community 21 - "类型注解规范"
Cohesion: 0.40
Nodes (4): 基本规则, 类型存根, 类型检查, 类型注解规范

### Community 23 - "deb 解包"
Cohesion: 0.40
Nodes (5): deb 解包, 内部结构 [推荐实践], 捆绑库处理 [推荐实践], 清理冗余文件 [推荐实践], 解包与清理 [推荐实践]

### Community 24 - "DLAGENTS 自定义下载代理 [推荐实践]"
Cohesion: 0.40
Nodes (5): DLAGENTS 自定义下载代理 [推荐实践], 参考, 常见陷阱, 格式与变量, 示例：URL 签名（linuxqq-nt）

### Community 27 - "源码编译"
Cohesion: 0.40
Nodes (5): strip 与 debug 包 [推荐实践], VCS 包 [推荐实践], 构建标志 [推荐实践], 构建流程 [官方规范], 源码编译

### Community 28 - "post-commit"
Cohesion: 0.40
Nodes (4): post-commit script, GRAPHIFY_CHANGED, GRAPHIFY_REBUILD_LOG, PYTHONHASHSEED

### Community 29 - "linuxqq-get-url.sh"
Cohesion: 0.70
Nodes (4): _fetch_route_cookie(), _resolve_deb_url(), linuxqq-get-url.sh script, _sign_url()

### Community 30 - "structure/"
Cohesion: 0.40
Nodes (4): structure/, 命名, 添加新包快照, 用途

### Community 31 - "版本 [官方规范]"
Cohesion: 0.50
Nodes (4): epoch, pkgrel, pkgver, 版本 [官方规范]

### Community 32 - "依赖 [官方规范]"
Cohesion: 0.50
Nodes (4): 依赖 [官方规范], 虚拟包 [推荐实践], 运行时加载依赖 [推荐实践], 预编译二进制包的依赖分析 [推荐实践]

### Community 33 - "post-checkout"
Cohesion: 0.50
Nodes (3): post-checkout script, GRAPHIFY_REBUILD_LOG, PYTHONHASHSEED

### Community 34 - "linuxqq.sh"
Cohesion: 0.50
Nodes (3): QQ_DEFAULT_FLAGS, QQ_USER_FLAGS, linuxqq.sh script

### Community 35 - "navicat17-premium-zh-cn"
Cohesion: 0.50
Nodes (3): Feedback, Install, navicat17-premium-zh-cn

### Community 36 - "trae-sg"
Cohesion: 0.50
Nodes (3): Feedback, Install, trae-sg

### Community 37 - "trae-us"
Cohesion: 0.50
Nodes (3): Feedback, Install, trae-us

### Community 39 - "PKGBUILDEditor"
Cohesion: 0.12
Nodes (8): PKGBUILDEditor, Path, PKGBUILD 文件编辑器，支持上下文管理器自动保存, 获取当前校验和值。 arch=None 读取非架构特定 sums=()（arch=('any') 包），否则读取 sums_<arch>=()。, PKGBUILD 中不存在该算法的校验和时返回空字符串, TestPKGBUILDEditorContextManager, TestPKGBUILDEditorGetters, TestPKGBUILDEditorUpdate

### Community 40 - "zen-browser-twilight.sh"
Cohesion: 0.50
Nodes (3): MOZ_APP_LAUNCHER, zen-browser-twilight.sh script, ZEN_USER_FLAGS

### Community 41 - "test_base_parser.py"
Cohesion: 0.12
Nodes (24): _Concrete, Any, LogCaptureFixture, aur_metadata.parsers.base 单元测试：_arch_value、_parse_json_dict 缓存与结构变更日志。, 统一格式：标记语 + 解析器名 + 详情 + 响应片段, 非字符串 evidence 先 repr 再截断（None/bytes/子对象均可作证据）, JSON 解析失败（如 200 返回 HTML 错误页）走统一结构变更日志, 最小可实例化子类（实现抽象方法），用于测试基类行为 (+16 more)

### Community 44 - "NavicatParser"
Cohesion: 0.12
Nodes (22): NavicatParser, Navicat Premium CS 版本解析器：HTML 版本 + 配置注入 URL, 从 release-note HTML 中提取 ``Navicat ... (Linux) ... version X.Y.Z``, 从配置注入的 arch→URL 映射中取下载链接（与响应无关）, _html(), aur_metadata.parsers.navicat 单元测试, 构造 release-note HTML 片段, 正则 IGNORECASE：大小写不一也能匹配 (+14 more)

### Community 47 - "AUR 包已知问题"
Cohesion: 0.20
Nodes (9): AUR 包已知问题, makepkg 缓存冲突, Navicat（navicat17-premium-zh-cn）, tarball 内包含冗余文件, Trae 系列（trae / trae-sg / trae-us / trae-cn）, 修改本地源文件后 hash 不匹配, 捆绑 GCC 运行时库导致 ckg 索引崩溃, 捆绑 libsystemd 与系统 libmount 不兼容 (+1 more)

### Community 49 - "Update Packages Workflow"
Cohesion: 0.48
Nodes (7): Conventional Commits Standard, Push to AUR Workflow, Update Packages Workflow, .SRCINFO Sync Requirement, awsl1414/archlinux-package-action, github-actions-deploy-aur Action, Chinese DNS Resolution for cdn-go.cn

### Community 53 - "trae"
Cohesion: 0.50
Nodes (3): Feedback, Install, trae

### Community 54 - "config.py"
Cohesion: 0.16
Nodes (20): AsyncScheduler, os, 注意事项, AppConfig, DatabaseConfig, GithubConfig, HttpConfig, load_config() (+12 more)

### Community 59 - "linuxqq-nt"
Cohesion: 0.50
Nodes (3): Feedback, Install, linuxqq-nt

### Community 62 - "zen-browser-twilight-bin"
Cohesion: 0.50
Nodes (3): Feedback, Install, zen-browser-twilight-bin

### Community 63 - "test_api_packages.py"
Cohesion: 0.16
Nodes (23): description, get_package(), refresh_package(), ErrorCode, 业务错误码：前三位对齐 HTTP 状态码，后两位为子码, CollectThrottledError, DataNotReadyError, Exception (+15 more)

### Community 64 - "Package"
Cohesion: 0.11
Nodes (15): Package, 包采集配置（与 app/registry.py 的 PackageEntry 对应，由 DB 持久化）, PackageFileVersionParser, 安装包文件版本解析器基类：版本号从安装包文件本身提取。 适用场景：安装包（deb 等）自带权威版本元数据，比在文件名/页面上做正则 稳健。采集流程由…, 静态配置的各架构安装包 URL（arch_value → 原始 URL，未鉴权）。 返回 ``None`` 表示无静态配置，由服务层经版本源响应 +…, 从安装包文件头部字节提取版本号；结构不符返回 None 并记结构变更日志, 版本不来自文本响应，恒返回 None（实际提取走 ``version_from_package_head``）, 版本域：按解析器类型分派。 - 安装包解析器（``PackageFileVersionParser``，如 deb/QQ）：定位安装包 URL →… (+7 more)

### Community 65 - "extract_extension_from_url"
Cohesion: 0.13
Nodes (10): extract_extension_from_url(), extract_filename_from_url(), generate_download_filename(), 从 URL 中提取文件扩展名（包含点号） 支持复合扩展名（如 .tar.gz）和普通扩展名, 生成标准化的下载文件名 格式: {package_name}_{version}_{arch}{extension} 自动从 URL…, 从 URL 中提取文件名（包含扩展名） 支持处理查询参数和片段标识符, TestExtractExtensionFromUrl, TestExtractFilenameFromUrl (+2 more)

### Community 80 - "PackageService"
Cohesion: 0.13
Nodes (13): KeyError, PackageNotFoundError, PackageService, 该包是否处于采集节流窗口内（距上次采集不足最小间隔）, 剔除不在 ``keep`` 集合中的包的节流记录与采集锁。 reload 后已删除/停用的包不再采集，其运行时状态应清理，避免长生命周期下只增不减。, 纯 DB 读：返回最新成功版本快照 + 其所请求算法的各架构 hash。 无网络、不阻塞下载。version fetched_at 超过…, 从 DB 读最新成功 version + 其 hashes；无则返回 None。 urls 与 hashes 均以**当前** entry.archs…, fire-and-forget 触发后台采集：节流窗口内、正采集中或已有后台任务排队时跳过。 后台任务在下一 event-loop tick 才取锁，故并发… (+5 more)

### Community 81 - "test_response.py"
Cohesion: 0.10
Nodes (21): `PackageInfo`, `PackageList`, 数据模型, PackageList, BaseModel, _client_with(), endpoint(), aur_metadata.response 单元测试：成功响应构造与全局异常处理器接线。 (+13 more)

### Community 82 - "test_pypi_parser.py"
Cohesion: 0.13
Nodes (19): _payload(), Any, aur_metadata.parsers.pypi 单元测试, 构造 PyPI JSON 响应，可覆盖 info / urls, info 键存在但值为 null（限流/错误载荷）→ None 且不抛 AttributeError, sdist 与架构无关，任意 arch 返回同一 URL, 只取 packagetype=sdist，跳过 bdist, urls 键存在但值为 null → None 且不抛 TypeError (+11 more)

### Community 83 - ".fetch_and_hash_multi"
Cohesion: 0.13
Nodes (16): HTTPError, _describe_http_error(), _download_one(), _attempt(), _attempt(), _is_retryable(), T, 对瞬时网络错误按指数退避重试，非瞬时错误或耗尽后抛出由调用方记录。 - 瞬时错误（``_is_retryable``）：指数退避 ``backoff *… (+8 more)

### Community 84 - "aur-metadata"
Cohesion: 0.10
Nodes (19): API 路由文档, 业务码, 列出所有已注册包, 定时采集与数据库, 成功响应, 手动触发采集并落库, 查询指定包的最新版本与文件 hash, 统一响应结构 (+11 more)

### Community 85 - "test_qq_parser.py"
Cohesion: 0.11
Nodes (18): _payload(), Any, aur_metadata.parsers.qq 单元测试（纯解析逻辑，不触网络）, QQ 复用基类 _parse_json_dict 缓存，同一响应只 json 解析一次, 构造 QQ pcConfig 响应，可覆盖 Linux 段字段, deb control 段 Version 归一化：<upstream>_<revision>, deb 值非字符串（如嵌套 dict）→ None（防垃圾 URL 流入签名/下载环节）, arch 既可传 ArchEnum 也可传字符串值 (+10 more)

### Community 86 - ".load_from_yaml"
Cohesion: 0.21
Nodes (10): Path, 从 YAML 文件加载配置 Args: filepath: 配置文件路径；相对路径相对当前工作目录解析 Returns: 加载完成的…, Path, 全局默认 hash_algorithm 为 b2, 全局默认不忽略 SSL 错误（证书校验开启）, 空 YAML 文件抛出 ValueError, 不存在的文件抛出 FileNotFoundError, 基于 tmp_path 合成配置的自包含测试，不依赖仓库真实 config.yaml (+2 more)

### Community 87 - "compare_versions"
Cohesion: 0.17
Nodes (6): compare_versions(), parse_version(), 比较两个版本号 Args: version1: 第一个版本号 version2: 第二个版本号 Returns: -1: version1 <…, 解析版本号为可比较的组成部分 Args: version: 版本字符串，如 "3.2.22_251203", "17.3.5" Returns:…, TestCompareVersions, TestParseVersion

### Community 88 - "DebParseError"
Cohesion: 0.14
Nodes (20): DebParseError, parse_deb_control_version(), Exception, deb 头部结构不符合预期（magic/成员/control 缺失或损坏）, 从 deb 文件头部字节提取 control 的原始 ``Version`` 字段值。 只需覆盖到 control.tar 成员结束的前缀字节即可，data…, 解压 control.tar 成员并提取 ``Version`` 字段原始值, _version_from_control_tar(), 头部不足 60 字节成员头 → 视为无 control 成员 (+12 more)

### Community 89 - "test_fetcher_retry.py"
Cohesion: 0.15
Nodes (15): _make_fetcher(), counting_handler(), AsyncClient, Fetcher 重试机制单测。 用 ``httpx.MockTransport`` 模拟瞬时网络错误与可重试状态码，验证： - 瞬时错误后重试成功 →…, 流式下载持续 ReadTimeout → 重试至上限后返回 None。, 构造带 MockTransport 的 Fetcher，重试参数经 HttpConfig 注入。, 首次 ConnectError，第二次成功 → 返回文本，共调用 2 次。, 404 是确定性失败，不重试，仅调用 1 次。 (+7 more)

### Community 90 - "test_zen_parser.py"
Cohesion: 0.14
Nodes (17): _payload(), Any, parametrize, aur_metadata.parsers.zen 单元测试, assets 键存在但值为 null → None 且不抛 TypeError（helper 的 None 表默认，故直构）, 构造 GitHub Releases JSON 响应, release name 不含「数字.数字」片段 → None, 匹配到 asset 但无 browser_download_url → 继续找，最终 None (+9 more)

### Community 91 - "package_service.py"
Cohesion: 0.15
Nodes (14): apscheduler, collections_abc, contextlib, datetime, aur-metadata 服务入口：FastAPI 应用工厂与命令行入口, 包采集编排服务。 版本采集与 hash 下载是两个独立域：各自独立 fetch、独立事务落库。version 先行落库， 永不被 hash…, 版本快照是否超过 ``version_stale_seconds`` 视为过期, _utcnow() (+6 more)

### Community 92 - "load_packages"
Cohesion: 0.23
Nodes (18): _configure_logging(), main(), CLI 入口：加载配置并启动 uvicorn 服务, load_packages(), Path, 加载包采集配置文件（TOML，``[[packages]]`` 数组）。 路径解析优先级：显式参数 > 环境变量 ``APP_PACKAGES`` >…, Path, 仓库默认 packages.toml 必须始终可加载且包集合符合预期（防配置回退）。 逐一断言各 trae 的 region：[[packages]]… (+10 more)

### Community 93 - "PackageConfig"
Cohesion: 0.15
Nodes (9): PackageConfig, 单个包的配置。 ``name`` 为 ``aur-metadata`` 中注册的包名（用于拼接 API 查询 URL）。, 将字符串架构列表转换为 ArchEnum 列表, 获取生效的哈希算法（包级覆盖 > 全局默认）, model_config extra=ignore：传入额外字段字典时被忽略, hash_algorithm 为 None 时使用全局默认, hash_algorithm 显式设置时覆盖全局默认, TestPackageConfig (+1 more)

### Community 103 - "test_fetcher_head.py"
Cohesion: 0.20
Nodes (12): _make_fetcher(), counting_handler(), Fetcher.fetch_head 单测：Range 头、流式截断与重试语义。, 构造带 MockTransport 的 Fetcher：零退避，尝试次数可调（经 HttpConfig 注入）, 只返回前 max_bytes 字节，且请求携带 Range 头, 响应体不足 max_bytes → 原样返回全部, test_fetch_head_404_returns_none(), test_fetch_head_invalid_max_bytes_raises() (+4 more)

### Community 105 - "PackageVersion"
Cohesion: 0.16
Nodes (10): Model, Meta, PackageHash, PackageVersion, 版本快照：版本采集域，与 hash 采集解耦独立落库, 文件 hash：版本快照下「架构 × 算法」粒度的记录，逐架构独立成败, _HashResult, hash 域：逐 arch resolve_raw_url（QQ 签名）→ 并发下载一次算全部算法 → 逐行落库。 每个架构单次下载同时产出全部… (+2 more)

### Community 106 - "models/__init__.py"
Cohesion: 0.16
Nodes (12): Tortoise ORM 模型：定时采集结果库。 字段与 ``db/schema.sql`` 对齐——schema.sql 是结构的事实来源， 本模块仅作为…, db(), make_package(), Any, fixture, Path, qq_response(), 共享测试夹具。 约定： - DB 夹具用临时文件 SQLite + ``Tortoise.generate_schemas``，函数级隔离； 不复用生产… (+4 more)

### Community 107 - "package_updater.py"
Cohesion: 0.14
Nodes (17): argparse, asyncio, functools, Namespace, pathlib, _configure_logging(), _dispatch(), main() (+9 more)

### Community 108 - "QQParser"
Cohesion: 0.15
Nodes (11): Any, QQParser, 对原始 deb 链接签名，返回带 sign 的可直接下载 URL（QQ 鉴权）。 返回的 URL 已带 sign 查询参数，可直接用于流式下载并计算校验和；…, QQ Linux 版本解析器：版本取自 deb control 段，URL 需 GetSign 签名 安装包 URL…, 取指定架构的 deb 下载 URL；字段值为 dict 取 ``deb`` 键，为裸字符串直接用。 归一化后强制 str…, 从 QQ 响应数据中提取指定架构的下载 URL（原始未签名链接）, 对指定 deb 链接换取带 sign 的临时链接。 流程： 1) 请求 im.qq.com/index/ 获取 tgw_l7_route cookie 2)…, _entry() (+3 more)

### Community 112 - "aur_metadata/utils/hash.py"
Cohesion: 0.20
Nodes (10): hashlib, get_hash_builder(), _Hash, Protocol, 返回指定算法的 hash 构造器。 供流式下载边下边算场景复用；不支持算法时抛 ValueError。, aur_metadata.utils.hash 单元测试, b2/sha256/sha512 各返回对应构造器，且计算结果与 hashlib 一致, test_get_hash_builder_case_insensitive() (+2 more)

### Community 113 - "._update_scalar_field"
Cohesion: 0.14
Nodes (4): 更新校验和字段。 arch=None 更新非架构特定 sums=()（arch=('any') 包），否则更新 sums_<arch>=()。, 替换 ^field=.*$ 整行为 field=value（MULTILINE）。字段不存在时无操作。 用 lambda 返回替换文本，避免 value…, 返回 ^field=(.*)$ 的捕获值；字段不存在返回 None。, 取标量并按 int 解析；缺失或解析失败返回 default。

### Community 114 - "PackageInfo"
Cohesion: 0.20
Nodes (8): PackageInfo, 包信息：版本号 + 各架构原始下载 URL + 文件 hash, 手动触发采集；异常上抛供路由层转 HTTP 错误。 节流由 PackageService 判定（持 per-package 锁，消除 check-then-…, FakePackageService, FakeScheduleService, Exception, 可控 PackageService：按预设行为驱动 get_package / list_packages, 可控 ScheduleService：驱动 refresh_package / reload_packages

### Community 115 - "response.py"
Cohesion: 0.21
Nodes (11): fastapi_exceptions, fastapi_responses, http, _envelope(), FastAPI, register_exception_handlers(), _handle_biz_error(), _handle_unhandled() (+3 more)

### Community 116 - "calculate_file_hash"
Cohesion: 0.27
Nodes (7): calculate_file_hash(), Path, 计算文件哈希值 支持 BLAKE2b(b2)、SHA512、SHA256 算法，分块读取大文件避免内存占用过高, Path, calculate_file_hash 测试, 文件不存在抛出 FileNotFoundError, TestCalculateFileHash

### Community 118 - "DebParser"
Cohesion: 0.15
Nodes (10): DebParser, 通用 deb 包解析器：URL 静态配置，版本取自 control 段, 返回配置注入的各架构安装包 URL（静态，版本域无需版本源响应）, 从配置映射取指定架构链接（与响应无关）；缺架构属配置错误走普通日志。 服务层静态路径直接消费…, deb 架构别名（amd64/arm64/loongarch64）归一化为 ArchEnum 值, 直接使用 ArchEnum 值作键时不做改写, parser_type=deb 经注册表构造，且具备安装包版本解析能力, test_get_parser_deb_with_config() (+2 more)

### Community 119 - "PackageEntry"
Cohesion: 0.18
Nodes (8): PackageEntry, PackageRegistry, 包注册表：内存中的可查询包集合，由 DB 加载（replace_all）构建。 新增/修改包只需操作 ``packages`` 表并调用…, 用给定列表整体替换注册表内容（用于从 DB 重新加载）, replace_all 整体替换，旧条目被清空, list_all 返回列表副本，外部修改不影响内部存储, test_list_all_returns_copy(), test_replace_all_rebuilds_from_scratch()

### Community 120 - "test_deb_parser.py"
Cohesion: 0.17
Nodes (11): build_deb(), 构造最小合法 deb（ar + debian-binary + control.tar.<compression>）。…, aur_metadata.parsers.deb 单元测试：DebParser 配置注入与 deb 头部版本提取。, 版本不来自文本响应（契约：服务层走 version_from_package_head）, test_parse_url_from_config(), test_parse_version_always_none(), test_version_from_package_head_success(), control 成员名为 ``control``（无 ./ 前缀变体）同样可提取 (+3 more)

### Community 121 - "ApiResponse"
Cohesion: 0.20
Nodes (12): PackageServiceDep, post, list_packages(), 新增/修改/删除 packages 行后调用，使 registry 与 schedule 即时对齐 DB。 返回重载后 enabled…, reload_packages(), ApiResponse, BaseModel, T (+4 more)

### Community 122 - "config_loader.py"
Cohesion: 0.20
Nodes (9): ApiSettings, ConfigLoader, DownloadSettings, BaseModel, 配置加载器，管理全局设置和包配置 ``base_dir`` 为配置文件所在目录，配置内的相对路径（如 ``pkgbuild``） 均以该目录为基准解析。, Settings, _Hash, Protocol (+1 more)

### Community 123 - "_make_downloader"
Cohesion: 0.21
Nodes (8): _make_downloader(), Any, Downloader 单元测试（aria2c 参数拼装）, 构造 Downloader，mock 掉 aria2c 存在性检查（CI 环境可能未安装）, 默认开启证书校验（--check-certificate=true）, check_certificate=False 时传给 aria2c --check-certificate=false, TestBuildBaseArgs, unittest_mock

### Community 124 - "fakes.py"
Cohesion: 0.31
Nodes (8): gzip, io, lzma, deb 包版本提取工具。 从 deb 文件**头部字节**解析 control 段的 ``Version`` 字段——版本号位于第二个 ar 成员…, 测试用桩：可控解析器、Fetcher 与 registry 构造，避免真实网络。 放普通模块而非 conftest，便于测试用绝对导入（``from…, aur_metadata.utils.deb 单元测试：ar 解析、control.tar 解压与版本归一化。, tarfile, zstandard

### Community 125 - "._update_source_field"
Cohesion: 0.25
Nodes (4): 文本是否包含 shell 变量引用（${VAR} 或 $VAR/$_VAR）, source 条目是否为远程 URL（带 :: 别名或以协议头开头）, 更新 source / source_<arch> 字段的远程 URL。 - 支持单行/多行、单条目/多条目数组；本地源条目（如…, 更新 source URL，保留别名与本地源条目；URL 含 shell 变量时跳过。 arch=None 更新非架构特定…

### Community 126 - "Downloader"
Cohesion: 0.29
Nodes (5): Downloader, DownloadResult, Path, 基于 aria2c 的异步下载器 特性： - 多连接分片下载（aria2c -x/-s） - 断点续传（aria2c -c） -…, 使用单个 aria2c 实例批量下载多个文件 Args: downloads: {arch: (url, file_path)} 字典…

### Community 127 - "TestPKGBUILDEditorEpoch"
Cohesion: 0.25
Nodes (4): update_epoch 和 get_epoch 测试, 无 epoch 行时在 pkgver 前插入, new_epoch=None 时不做任何修改, TestPKGBUILDEditorEpoch

### Community 128 - "normalize_deb_version"
Cohesion: 0.25
Nodes (7): 从 deb 头部字节提取 ``[epoch:]upstream[-revision]`` 并归一化。 归一化规则（下游 pkgver 不接受…, normalize_deb_version(), 将 deb ``Version`` 字段（``[epoch:]upstream[-revision]``）归一化为服务版本号。 - 去…, parametrize, 四种 control.tar 编码均能提取原始 Version 字段, test_normalize_deb_version(), test_parse_control_version_all_compressions()

### Community 129 - "._json_section"
Cohesion: 0.43
Nodes (4): Any, 解析 JSON 响应为 dict 并按 ``response_data`` 缓存。 非 dict 结构或解析失败返回…, 统一记录「疑似上游数据结构变更」告警。 响应内容偏离 parser 预期结构时调用——通常是上游 API/页面改版。 统一格式（解析器名 + 详情 +…, 按路径取嵌套 dict 段（如 ``data.manifest.linux``）。 任一级缺失或非 dict 返回 None 并记结构变更日志，统一各…

### Community 130 - "注释规范"
Cohesion: 0.33
Nodes (5): 注释规范, 示例, 自检, 规则, 风格细节

### Community 131 - "PyPIParser"
Cohesion: 0.33
Nodes (4): PyPIParser, PyPI 包解析器：``info.version`` 取版本，``urls[]`` 中 sdist 取 URL, 从 PyPI JSON 的 ``info.version`` 提取版本号。 ``info`` 键存在但值为 null（限流/错误载荷）时…, 从 ``urls[]`` 中取 ``packagetype=="sdist"`` 的下载链接

### Community 132 - "ZenParser"
Cohesion: 0.33
Nodes (4): Zen Browser 每夜版解析器：GitHub Releases JSON 提取版本与 asset 链接, 从 release ``name`` 提取版本号，有日期则拼为 ``version.YYYYMMDD``, 从 ``assets[]`` 中按名称匹配指定架构的 ``browser_download_url``, ZenParser

### Community 133 - "aur-metadata/AGENTS.md"
Cohesion: 0.40
Nodes (3): 开发命令, 目录结构, 项目定位

### Community 134 - "test_parse_url_unknown_arch_warns_and_none"
Cohesion: 0.40
Nodes (5): LogCaptureFixture, 未配置的架构属配置错误 → 普通告警 + None, 非 deb 结构 → None 且走统一结构变更日志, test_parse_url_unknown_arch_warns_and_none(), test_version_from_package_head_bad_structure()

### Community 135 - "test_parse_url_region_selection"
Cohesion: 0.40
Nodes (5): parametrize, 不同 region 取对应机房 CDN 链接, 各架构链接版本不一致时拒绝返回，防 hash 挂错版本号, test_parse_url_region_selection(), test_parse_version_cross_arch_consistency()

### Community 136 - "test_version_from_package_head_bad_structure"
Cohesion: 0.67
Nodes (3): LogCaptureFixture, 头部非 deb 结构 → None 且走统一结构变更日志, test_version_from_package_head_bad_structure()

## Knowledge Gaps
- **157 isolated node(s):** `linuxqq.sh script`, `QQ_DEFAULT_FLAGS`, `QQ_USER_FLAGS`, `navicat.sh script`, `LD_PRELOAD` (+152 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 695 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **71 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ArchEnum` connect `ArchEnum` to `test_package_seeder.py`, `PyPIParser`, `ZenParser`, `test_package_service.py`, `test_parse_url_unknown_arch_warns_and_none`, `test_schedule_service.py`, `test_parse_url_region_selection`, `PackageUpdater`, `TraeParser`, `test_package_service_deb.py`, `test_base_parser.py`, `NavicatParser`, `PackageService`, `test_pypi_parser.py`, `test_qq_parser.py`, `test_zen_parser.py`, `package_service.py`, `PackageConfig`, `package_updater.py`, `QQParser`, `DebParser`, `PackageEntry`, `test_deb_parser.py`, `config_loader.py`?**
  _High betweenness centrality (0.178) - this node is a cross-community bridge._
- **Why does `PKGBUILDEditor` connect `PKGBUILDEditor` to `.__exit__`, `Path`, `PackageUpdater`, `package_updater.py`, `._update_scalar_field`, `._update_source_field`, `TestPKGBUILDEditorEpoch`?**
  _High betweenness centrality (0.109) - this node is a cross-community bridge._
- **Why does `pkgbuild()` connect `AUR 包自动更新工具` to `package_updater.py`, `Path`?**
  _High betweenness centrality (0.103) - this node is a cross-community bridge._
- **Are the 49 inferred relationships involving `ArchEnum` (e.g. with `PackageUpdater` and `PackageConfig`) actually correct?**
  _`ArchEnum` has 49 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `PKGBUILDEditor` (e.g. with `PackageUpdater` and `HashAlgorithmEnum`) actually correct?**
  _`PKGBUILDEditor` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `PackageService` (e.g. with `get_package_service()` and `lifespan()`) actually correct?**
  _`PackageService` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `BaseParser` (e.g. with `ArchEnum` and `AppConfig`) actually correct?**
  _`BaseParser` has 10 INFERRED edges - model-reasoned connections that need verification._