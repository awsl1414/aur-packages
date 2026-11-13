# Graph Report - aur-packages  (2026-11-13)

## Corpus Check
- 136 files · ~49,706 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 50 file(s) not represented in the graph (top: (none) 33, .install 7, .desktop 6)
- WARNING: 50 of 192 files seen (26%) have no supported extractor and are missing from this graph entirely. It may look complete while representing only part of the codebase.

## Summary
- 1848 nodes · 3596 edges · 190 communities (96 shown, 94 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 400 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e59abccf`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_package_seeder.py
- Path
- PackageConfig
- PackageUpdater
- .load_from_yaml
- calculate_file_hash
- AUR 打包实践指南
- PackageUpdater
- ApiParser
- compare_versions
- pytest
- fakes.py
- packages.py
- 设计
- TestPKGBUILDEditorEpoch
- test_package_service_deb.py
- aur_metadata/cli.py
- AppImage 解包
- Electron 直装（tarball）
- 类型注解规范
- CONTRIBUTORS List
- deb 解包
- DLAGENTS 自定义下载代理 [推荐实践]
- aur-auto-update
- linuxqq-nt Package
- 源码编译
- linuxqq-get-url.sh
- structure/
- 版本 [官方规范]
- 依赖 [官方规范]
- linuxqq.sh
- navicat17-premium-zh-cn
- trae-sg
- trae-us
- keep-alive.yml
- test_package_updater_checksums.py
- zen-browser-twilight.sh
- package_updater.py
- navicat.sh
- trae-cn.sh
- test_rule_parser.py
- CLAUDE.md Project Instructions
- linuxqq-nt package (Electron QQ)
- BaseParser
- update-packages.yml
- trae-sg/trae.sh
- trae/trae.sh
- trae-us/trae.sh
- trae
- PKGBUILDEditor
- CONTRIBUTING Guide
- README - AUR Package Auto-Updater
- linuxqq-nt
- CONTRIBUTORS.md
- BaseParser Plugin Pattern
- zen-browser-twilight-bin
- test_api_packages.py
- aur_metadata/config.py
- generate_download_filename
- navicat17-premium-zh-cn Package
- trae Package (China CDN)
- trae-cn Package (Domestic)
- trae-sg Package (Singapore CDN)
- trae-us Package (US CDN)
- AppConfig
- response.py
- PKGBUILDEditor
- .fetch_head
- API 路由文档
- test_qq_parser.py
- db/__init__.py
- tests/__init__.py
- ._add_schedule
- aur_metadata/config.py
- PackageService
- LogCaptureFixture
- blake2b hash builder registration (_HASH_BUILDERS)
- get_effective_hash_algorithm method
- hash_algorithm config field (Settings + PackageConfig override)
- PackageUpdater hardcoded SHA512 elimination
- PKGBUILDEditor hash_algorithm parameterization
- B2 unit tests (hash + pkgbuild_editor)
- aria2c Multi-threaded Downloader
- makepkg Build Tool
- namcap PKGBUILD Linter
- github_release_service.py
- uv Package Manager
- _service
- db/__init__.py
- .get_checksum
- PackageRegistry
- navicat17-premium-zh-cn package (Chinese Simplified)
- Trae AI IDE by ByteDance (CDN variants)
- zen-browser-twilight-bin package (Firefox-based nightly)
- models/__init__.py
- test_fetcher.py
- load_config
- make_app_config
- TestGithubSourceConfig
- HashAlgorithmEnum (SHA256/SHA512/B2)
- DebParser
- refresh_package
- version
- with
- package_updater.py
- Fetcher
- PackageList
- PackageConfig
- z-code.sh
- aur_auto_update/fetcher.py
- ArchEnum
- 注释规范
- _Hash
- ArchEnum
- commit
- pytest
- z-code
- steps
- aur-metadata
- aur-packages
- packages
- bt-dualboot-ng
- download
- linuxqq-nt
- navicat
- orca-ide
- rustmusic
- trae
- trae-cn
- trae-sg
- asyncio
- README.md
- aur-metadata
- trae-us
- z-code
- zen-browser
- ParsedPackage
- push-to-aur
- .version_from_package_head
- generate-srcinfo
- on
- aur_auto_update/config.py
- _zcode_parser

## God Nodes (most connected - your core abstractions)
1. `PKGBUILDEditor` - 60 edges
2. `PackageService` - 40 edges
3. `AppConfig` - 37 edges
4. `PackageConfig` - 36 edges
5. `Fetcher` - 36 edges
6. `RuleParser` - 33 edges
7. `ApiParser` - 32 edges
8. `BaseParser` - 32 edges
9. `PackageUpdater` - 30 edges
10. `make_app_config()` - 29 edges

## Surprising Connections (you probably didn't know these)
- `第 3 步：配置 updater` --references--> `pkgbuild()`  [INFERRED]
  docs/adding-a-package.md → projects/aur-auto-update/tests/test_pkgbuild_editor.py
- `Push to AUR Workflow` --implements--> `Conventional Commits Standard`  [INFERRED]
  .github/workflows/push-to-aur.yml → CLAUDE.md
- `Push to AUR Workflow` --implements--> `.SRCINFO Sync Requirement`  [INFERRED]
  .github/workflows/push-to-aur.yml → docs/packaging-guide.md
- ``PackageInfo`` --references--> `PackageInfo`  [INFERRED]
  projects/aur-metadata/docs/api.md → projects/aur-metadata/src/aur_metadata/schemas.py
- `定时采集与数据库` --references--> `success()`  [INFERRED]
  projects/aur-metadata/docs/api.md → projects/aur-metadata/src/aur_metadata/response.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **B2 hash support implementation flow (Enum → Config → Updater)** — specs_hash_algorithm_enum, specs_blake2b_builder, specs_hash_algorithm_field, specs_pkgbuild_editor_api, specs_package_updater_hardcode_removal [EXTRACTED 0.95]
- **Update → SRCINFO → Commit → AUR Push Pipeline** — github_workflows_update_packages, wf_arch_pkg_action, wf_aur_deploy_action, rules_srcinfo [INFERRED 0.85]
- **makepkg checksum / cache-busting rule cluster** — rules_source_alias_cache, rules_carch_in_source, rules_local_source_hash, rules_rolling_release_checksum, tool_makepkg [INFERRED 0.85]

## Communities (190 total, 94 thin omitted)

### Community 0 - "test_package_seeder.py"
Cohesion: 0.17
Nodes (15): sync_packages_from_config(), SyncReport, _cfg(), _get(), test_sync_creates_packages(), test_sync_cron_schedule(), test_sync_disabled_new_package(), test_sync_keeps_orphan_packages() (+7 more)

### Community 1 - "Path"
Cohesion: 0.05
Nodes (6): PKGBUILDEditor, TestPKGBUILDEditorEdgeCases, TestPKGBUILDEditorGetters, TestPKGBUILDEditorUpdate, TestUpdateSourceArchEdgeCases, TestUpdateSourceEdgeCases

### Community 3 - "PackageConfig"
Cohesion: 0.07
Nodes (21): FakeParser, make_qq_registry(), _build_service(), _cfg(), FakeScheduler, _pkg(), _svc(), test_build_trigger_cron() (+13 more)

### Community 4 - "PackageUpdater"
Cohesion: 0.15
Nodes (7): list_packages(), refresh_package(), reload_packages(), ApiResponse, success(), CollectThrottledError, test_refresh_throttled()

### Community 8 - "AUR 打包实践指南"
Cohesion: 0.13
Nodes (15): AUR 打包实践指南, license [官方规范], pkgdesc [官方规范], provides 和 conflicts [推荐实践], Shell 补全 [推荐实践], source 声明 [推荐实践], .SRCINFO [官方规范], 代码质量 [推荐实践] (+7 more)

### Community 9 - "PackageUpdater"
Cohesion: 0.12
Nodes (3): _dispatch(), PackageUpdater, UpdateSummary

### Community 10 - "ApiParser"
Cohesion: 0.10
Nodes (5): ApiParser, TestApiParseDownloadUrls, TestApiParseSuccess, TestApiParseUrls, TestApiParseVersionFailures

### Community 11 - "compare_versions"
Cohesion: 0.11
Nodes (18): TraeParser, _entry(), _payload(), test_default_region_is_cn(), test_parse_url_download_not_list(), test_parse_url_each_arch(), test_parse_url_region_not_present(), test_parse_url_region_selection() (+10 more)

### Community 12 - "pytest"
Cohesion: 0.10
Nodes (20): FakeFetcher, _service(), test_collect_version_fetch_failure_records_and_raises(), test_collect_version_new_version_inserts_row(), test_collect_version_now_info_has_empty_download_urls(), test_collect_version_now_throttled(), test_collect_version_now_unknown_package(), test_collect_version_persists_snapshot() (+12 more)

### Community 13 - "fakes.py"
Cohesion: 0.29
Nodes (6): Commit 规范, graphify, 开发命令, 注意事项, 添加新软件包, 项目结构（uv workspace monorepo）

### Community 14 - "packages.py"
Cohesion: 0.22
Nodes (4): get_package_service(), get_schedule_service(), BizError, ErrorCode

### Community 15 - "设计"
Cohesion: 0.15
Nodes (12): 1. HashAlgorithmEnum 新增 B2, 2. 注册 blake2b 构建器, 3. 配置模型新增 hash_algorithm 字段, 4. config.yaml 配置, 5. PKGBUILDEditor API 清理, 6. PackageUpdater 消除硬编码, 7. 单元测试补充, B2 (BLAKE2b) 哈希算法支持设计 (+4 more)

### Community 16 - "TestPKGBUILDEditorEpoch"
Cohesion: 0.10
Nodes (13): get_parser(), test_get_parser_deb_with_urls_config(), test_get_parser_empty_config_is_no_arg(), test_get_parser_returns_new_instance(), test_get_parser_rule_deb_needs_no_version_config(), test_get_parser_rule_invalid_config_raises(), test_get_parser_rule_requires_version_config(), test_get_parser_rule_with_rules_config() (+5 more)

### Community 17 - "test_package_service_deb.py"
Cohesion: 0.12
Nodes (13): _deb_service(), _DynamicDebParser, _make_deb_package(), _registry(), test_collect_deb_bad_structure_records_and_raises(), test_collect_deb_cross_arch_version_mismatch(), test_collect_deb_dynamic_url_source_failure(), test_collect_deb_dynamic_urls_fetch_text_once() (+5 more)

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

### Community 39 - "test_package_updater_checksums.py"
Cohesion: 0.22
Nodes (8): DownloadResult, _FakeDownloader, _parsed(), test_get_checksums_falls_back_to_urls(), test_get_checksums_no_url_skips_arch(), test_get_checksums_partial_arch_without_url_fails(), test_get_checksums_prefers_download_urls(), _updater()

### Community 40 - "zen-browser-twilight.sh"
Cohesion: 0.50
Nodes (3): MOZ_APP_LAUNCHER, zen-browser-twilight.sh script, ZEN_USER_FLAGS

### Community 41 - "package_updater.py"
Cohesion: 0.08
Nodes (14): _Concrete, test_arch_value_from_enum(), test_arch_value_from_string(), test_cache_bad_json_not_reparsed(), test_cache_hits_same_response_object(), test_cache_invalidates_on_new_response(), test_invalid_json_logged_as_structure_change(), test_log_structure_change_format() (+6 more)

### Community 44 - "test_rule_parser.py"
Cohesion: 0.11
Nodes (22): RuleParser, _rule(), _static_urls(), test_css_selector(), test_first_false_joins_all_hits(), test_invalid_rule_raises(), test_invalid_url_rule_raises(), test_jmespath() (+14 more)

### Community 47 - "BaseParser"
Cohesion: 0.22
Nodes (9): AUR 包已知问题, makepkg 缓存冲突, Navicat（navicat17-premium-zh-cn）, tarball 内包含冗余文件, Trae 系列（trae / trae-sg / trae-us / trae-cn）, 修改本地源文件后 hash 不匹配, 捆绑 GCC 运行时库导致 ckg 索引崩溃, 捆绑 libsystemd 与系统 libmount 不兼容 (+1 more)

### Community 49 - "update-packages.yml"
Cohesion: 0.12
Nodes (15): Conventional Commits Standard, Push to AUR Workflow, concurrency, cancel-in-progress, group, env, AUR_EMAIL, AUR_USERNAME (+7 more)

### Community 53 - "trae"
Cohesion: 0.50
Nodes (3): Feedback, Install, trae

### Community 54 - "PKGBUILDEditor"
Cohesion: 0.40
Nodes (3): 开发命令, 目录结构, 项目定位

### Community 59 - "linuxqq-nt"
Cohesion: 0.50
Nodes (3): Feedback, Install, linuxqq-nt

### Community 62 - "zen-browser-twilight-bin"
Cohesion: 0.50
Nodes (3): Feedback, Install, zen-browser-twilight-bin

### Community 63 - "test_api_packages.py"
Cohesion: 0.13
Nodes (16): get_package(), DataNotReadyError, FakePackageService, FakeScheduleService, _info(), _svc_pkg(), _svc_refresh(), _svc_sched() (+8 more)

### Community 64 - "aur_metadata/config.py"
Cohesion: 0.11
Nodes (6): QQConfig, ArchEnum, QQParser, get_parser_types(), RuleDebParser, test_parse_version_always_none()

### Community 65 - "generate_download_filename"
Cohesion: 0.13
Nodes (7): extract_extension_from_url(), extract_filename_from_url(), generate_download_filename(), _sanitize_component(), TestExtractExtensionFromUrl, TestExtractFilenameFromUrl, TestGenerateDownloadFilename

### Community 80 - "AppConfig"
Cohesion: 0.13
Nodes (6): 注意事项, AppConfig, _build_rule(), ExtractRule, _sorted_kinds(), _validate_expr_syntax()

### Community 81 - "response.py"
Cohesion: 0.10
Nodes (14): _envelope(), register_exception_handlers(), _handle_biz_error(), _handle_unhandled(), _handle_validation_error(), _client_with(), endpoint(), test_api_response_generic_roundtrip() (+6 more)

### Community 82 - "PKGBUILDEditor"
Cohesion: 0.16
Nodes (6): _app_version(), create_app(), _config(), _package(), test_lifespan_assembles_services_and_seeds(), test_openapi_version_from_package_metadata()

### Community 83 - ".fetch_head"
Cohesion: 0.17
Nodes (4): _describe_http_error(), _attempt(), _is_retryable(), _with_github_auth()

### Community 84 - "API 路由文档"
Cohesion: 0.18
Nodes (11): API 路由文档, 业务码, 列出所有已注册包, 定时采集与数据库, 成功响应, 手动触发采集并落库, 查询指定包的最新版本与下载 URL, 统一响应结构 (+3 more)

### Community 85 - "test_qq_parser.py"
Cohesion: 0.06
Nodes (14): _make_downloader(), TestBuildBaseArgs, TestStaleFileCleanup, TestUrlSafety, _payload(), test_parse_url_accepts_string_arch(), test_parse_url_loongarch_as_plain_string(), test_parse_url_missing_arm_field() (+6 more)

### Community 86 - "db/__init__.py"
Cohesion: 0.11
Nodes (4): PackageConfig, TestHashAlgorithmValidation, TestPackageConfig, TestPackageConfigUnknownArch

### Community 87 - "tests/__init__.py"
Cohesion: 0.17
Nodes (4): compare_versions(), parse_version(), TestCompareVersions, TestParseVersion

### Community 88 - "._add_schedule"
Cohesion: 0.09
Nodes (5): lifespan(), SchedulerConfig, _parse_package_id(), ScheduleService, _task_id()

### Community 89 - "aur_metadata/config.py"
Cohesion: 0.16
Nodes (8): make_app_config(), _make_fetcher(), counting_handler(), test_no_retry_on_client_error_status(), test_retry_exhausted_returns_none(), test_retry_on_503_then_success(), test_retry_transient_then_success(), handler()

### Community 91 - "PackageService"
Cohesion: 0.07
Nodes (7): Package, Meta, PackageVersion, Meta, BaseParser, PackageFileVersionParser, _VersionSnapshot

### Community 93 - "LogCaptureFixture"
Cohesion: 0.70
Nodes (4): _structure_changed(), test_jmespath_non_str_result(), test_regex_no_match(), test_selector_no_match()

### Community 103 - "github_release_service.py"
Cohesion: 0.16
Nodes (3): _extract_asset_urls(), _extract_version(), GithubReleaseService

### Community 105 - "_service"
Cohesion: 0.15
Nodes (13): GithubSourceConfig, _pkg(), _service(), test_fixed_tag_url(), test_forbidden_not_retried(), test_github_headers_and_token(), test_missing_asset_fails(), test_non_retryable_status_fails() (+5 more)

### Community 106 - "db/__init__.py"
Cohesion: 0.15
Nodes (7): build_tortoise_config(), close_db(), get_db_url(), init_db(), _load_schema_sql(), _split_sql(), test_full_pipeline_with_real_schema_and_config()

### Community 108 - "PackageRegistry"
Cohesion: 0.13
Nodes (10): PackageEntry, PackageRegistry, load_registry_from_db(), _entry(), test_loads_valid_packages(), test_entry_holds_parser_instance(), test_entry_is_frozen(), test_get_hit_and_miss() (+2 more)

### Community 112 - "models/__init__.py"
Cohesion: 0.13
Nodes (4): _clean_config_env(), db(), make_package(), qq_response()

### Community 113 - "test_fetcher.py"
Cohesion: 0.13
Nodes (10): _response(), test_extract_message_from_error_body(), test_fetch_text_network_error_retried(), test_fetch_text_no_retry_when_max_retries_zero(), test_fetch_text_permanent_error_no_retry(), test_fetch_text_retryable_exhausted(), test_fetch_text_retryable_then_success(), test_fetch_text_success() (+2 more)

### Community 114 - "load_config"
Cohesion: 0.10
Nodes (22): main(), DatabaseConfig, load_config(), load_packages(), _resolve_path(), ServerConfig, test_default_from_member_dir(), test_default_from_repo_root() (+14 more)

### Community 115 - "make_app_config"
Cohesion: 0.20
Nodes (8): _make_fetcher(), counting_handler(), test_fetch_head_404_returns_none(), test_fetch_head_invalid_max_bytes_raises(), test_fetch_head_reads_prefix_and_sends_range(), handler(), test_fetch_head_retry_transient_then_success(), test_fetch_head_short_body_returns_all()

### Community 118 - "DebParser"
Cohesion: 0.12
Nodes (9): DebControlVersionMixin, DebParser, test_get_parser_deb_with_config(), test_parse_url_from_config(), test_parse_url_unknown_arch_warns_and_none(), test_urls_canonical_keys_passthrough(), test_urls_deb_arch_aliases_normalized(), test_version_from_package_head_bad_structure() (+1 more)

### Community 119 - "refresh_package"
Cohesion: 0.11
Nodes (6): PackageInfo, PackageNotFoundError, PackageService, _utcnow(), test_collect_version_parse_failure_records(), test_get_info_urls_aligns_with_current_archs()

### Community 120 - "version"
Cohesion: 0.21
Nodes (13): aarch64, x86_64, assets, repo, tag, version, github, github (+5 more)

### Community 121 - "with"
Cohesion: 0.10
Nodes (20): with, assets, cache-dependency-glob, commit_email, commit_message, commit_username, enable-cache, flags (+12 more)

### Community 123 - "Fetcher"
Cohesion: 0.22
Nodes (5): _debug_extract(), _run(), GithubConfig, HttpConfig, Fetcher

### Community 124 - "PackageList"
Cohesion: 0.22
Nodes (5): `PackageInfo`, `PackageList`, 数据模型, PackageList, test_success_envelope()

### Community 125 - "PackageConfig"
Cohesion: 0.20
Nodes (4): PackageConfig, _definition_fields(), _validate(), test_sync_idempotent()

### Community 129 - "ArchEnum"
Cohesion: 0.25
Nodes (8): AUR 包自动更新工具, 开发, 快速开始, 技术栈, 支持的包, 特性, 许可证, 贡献

### Community 130 - "注释规范"
Cohesion: 0.33
Nodes (5): 注释规范, 示例, 自检, 规则, 风格细节

### Community 133 - "ArchEnum"
Cohesion: 0.40
Nodes (5): Commit 规范, 分支策略, 提交流程, 添加新软件包, 贡献指南

### Community 134 - "commit"
Cohesion: 0.18
Nodes (11): if, name, needs, runs-on, jobs, commit, update, changed_packages (+3 more)

### Community 135 - "pytest"
Cohesion: 0.11
Nodes (14): DebParseError, parse_deb_control_version(), _version_from_control_tar(), build_deb(), test_parse_accepts_trailing_bytes(), test_parse_bad_magic(), test_parse_control_member_missing_in_tar(), test_parse_control_name_without_dot_prefix() (+6 more)

### Community 136 - "z-code"
Cohesion: 0.50
Nodes (3): Feedback, Install, z-code

### Community 137 - "steps"
Cohesion: 0.31
Nodes (11): steps, GITHUB_TOKEN, steps, steps, env, id, if, name (+3 more)

### Community 140 - "packages"
Cohesion: 0.29
Nodes (6): base_url, packages, settings, api, hash_algorithm, ignore_ssl_errors

### Community 141 - "bt-dualboot-ng"
Cohesion: 0.33
Nodes (6): arch, enable, name, pkgbuild, update_source_url, bt-dualboot-ng

### Community 142 - "download"
Cohesion: 0.33
Nodes (6): connections, max_retries, retry_wait, show_progress, timeout, download

### Community 143 - "linuxqq-nt"
Cohesion: 0.33
Nodes (6): arch, enable, name, pkgbuild, update_source_url, linuxqq-nt

### Community 145 - "navicat"
Cohesion: 0.33
Nodes (6): arch, enable, name, pkgbuild, update_source_url, navicat

### Community 147 - "orca-ide"
Cohesion: 0.33
Nodes (6): arch, enable, name, pkgbuild, update_source_url, orca-ide

### Community 149 - "rustmusic"
Cohesion: 0.33
Nodes (6): rustmusic, arch, enable, name, pkgbuild, update_source_url

### Community 150 - "trae"
Cohesion: 0.33
Nodes (6): trae, arch, enable, name, pkgbuild, update_source_url

### Community 151 - "trae-cn"
Cohesion: 0.33
Nodes (6): trae-cn, arch, enable, name, pkgbuild, update_source_url

### Community 152 - "trae-sg"
Cohesion: 0.33
Nodes (6): trae-sg, arch, enable, name, pkgbuild, update_source_url

### Community 160 - "README.md"
Cohesion: 0.17
Nodes (10): 添加新软件包, 第 1 步：编写 PKGBUILD, 第 2 步：注册元数据采集, 第 3 步：配置 updater, 验证, aur-auto-update, 使用, 前置依赖 (+2 more)

### Community 161 - "aur-metadata"
Cohesion: 0.17
Nodes (10): aur-metadata, Docker 部署, 使用, 使用已发布镜像, 开发, 技术栈, 数据持久化, 本地构建镜像 (+2 more)

### Community 162 - "trae-us"
Cohesion: 0.33
Nodes (6): trae-us, arch, enable, name, pkgbuild, update_source_url

### Community 163 - "z-code"
Cohesion: 0.33
Nodes (6): z-code, arch, enable, name, pkgbuild, update_source_url

### Community 164 - "zen-browser"
Cohesion: 0.33
Nodes (6): zen-browser, arch, enable, name, pkgbuild, update_source_url

### Community 166 - "ParsedPackage"
Cohesion: 0.10
Nodes (12): ParsedPackage, PackageVersionProvider, _FakeFetcher, _FakeGithub, _pkg(), _provider(), test_fallback_failure_returns_none(), test_metadata_failure_falls_back_when_github_configured() (+4 more)

### Community 177 - "push-to-aur"
Cohesion: 0.22
Nodes (10): strategy, push-to-aur, package, if, name, needs, runs-on, strategy (+2 more)

### Community 181 - "generate-srcinfo"
Cohesion: 0.40
Nodes (5): if, name, needs, runs-on, generate-srcinfo

### Community 182 - "on"
Cohesion: 0.50
Nodes (4): on, schedule, workflow_dispatch, cron

### Community 187 - "aur_auto_update/config.py"
Cohesion: 0.12
Nodes (6): ApiSettings, ConfigLoader, DownloadSettings, Settings, _validate_hash_algorithm(), VersionRule

### Community 189 - "_zcode_parser"
Cohesion: 0.19
Nodes (5): test_rule_deb_parser_version_rule_not_required(), test_zcode_url_rule_fails_on_renamed_artifact(), test_zcode_url_rules_extract_both_archs(), test_zcode_version_from_package_head(), _zcode_parser()

## Knowledge Gaps
- **43 isolated node(s):** `aur-metadata`, `aria2c Multi-threaded Downloader`, `namcap PKGBUILD Linter`, `uv Package Manager`, `linuxqq-nt Package` (+38 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 894 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **94 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `pkgbuild()` connect `README.md` to `Path`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `PKGBUILDEditor` (e.g. with `TestPKGBUILDEditorEdgeCases` and `TestPKGBUILDEditorGetters`) actually correct?**
  _`PKGBUILDEditor` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aur-metadata`, `aria2c Multi-threaded Downloader`, `namcap PKGBUILD Linter` to the rest of the system?**
  _43 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Path` be split into smaller, more focused modules?**
  _Cohesion score 0.05195968645016797 - nodes in this community are weakly interconnected._
- **Why does `添加新软件包` connect `README.md` to `README.md`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `PackageService` (e.g. with `get_package_service()` and `lifespan()`) actually correct?**
  _`PackageService` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Should `PackageConfig` be split into smaller, more focused modules?**
  _Cohesion score 0.07205513784461152 - nodes in this community are weakly interconnected._