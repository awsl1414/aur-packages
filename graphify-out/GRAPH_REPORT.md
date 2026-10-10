# Graph Report - aur-packages  (2026-10-10)

## Corpus Check
- 124 files · ~47,322 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 49 file(s) not represented in the graph (top: (none) 32, .install 7, .desktop 6)

## Summary
- 1681 nodes · 3429 edges · 160 communities (78 shown, 82 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 417 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `682a53ba`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_package_seeder.py
- PKGBUILDEditor
- test_schedule_service.py
- get_package
- .load_from_yaml
- package_service.py
- AUR 打包实践指南
- PackageUpdater
- ApiParser
- json
- test_package_service.py
- AGENTS.md
- packages.py
- 设计
- get_parser
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
- linuxqq-get-url.sh
- structure/
- 版本 [官方规范]
- 依赖 [官方规范]
- linuxqq.sh
- navicat17-premium-zh-cn
- trae-sg
- trae-us
- Keep Repository Alive Workflow
- test_package_updater_checksums.py
- zen-browser-twilight.sh
- test_base_parser.py
- navicat.sh
- trae-cn.sh
- test_rule_parser.py
- CLAUDE.md Project Instructions
- linuxqq-nt package (Electron QQ)
- AUR 包已知问题
- Update Packages Workflow
- trae-sg/trae.sh
- trae/trae.sh
- trae-us/trae.sh
- trae
- aur-metadata/AGENTS.md
- CONTRIBUTING Guide
- README - AUR Package Auto-Updater
- linuxqq-nt
- CONTRIBUTORS.md
- BaseParser Plugin Pattern
- zen-browser-twilight-bin
- test_api_packages.py
- _validate
- generate_download_filename
- navicat17-premium-zh-cn Package
- trae Package (China CDN)
- trae-cn Package (Domestic)
- trae-sg Package (Singapore CDN)
- trae-us Package (US CDN)
- AppConfig
- response.py
- test_app_integration.py
- Fetcher
- API 路由文档
- test_qq_parser.py
- PackageConfig
- compare_versions
- Package
- _make_fetcher
- test_zen_parser.py
- PackageEntry
- load_config
- 二、aur-metadata 修复清单
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
- .collect_hashes
- CollectThrottledError
- downloader.py
- PackageRegistry
- navicat17-premium-zh-cn package (Chinese Simplified)
- Trae AI IDE by ByteDance (CDN variants)
- zen-browser-twilight-bin package (Firefox-based nightly)
- conftest.py
- 三、仓库根资产清单
- load_packages
- make_app_config
- calculate_file_hash
- HashAlgorithmEnum (SHA256/SHA512/B2)
- DebParser
- PackageService
- ConfigLoader
- rule.py
- package_updater.py
- aur_auto_update/cli.py
- FakeFetcher
- 一、aur-auto-update 修复清单
- z-code.sh
- _zcode_parser
- AUR 包自动更新工具
- 注释规范
- _validate_hash_algorithm
- make_qq_registry
- 贡献指南
- PackageInfo
- pytest
- z-code
- _Hash
- aur-metadata
- aur-packages
- load_registry_from_db
- test_rule_deb_parser_version_from_package_head
- aur_metadata/cli.py
- 添加新软件包
- aur-metadata
- ._handle_version_update
- 统一响应结构

## God Nodes (most connected - your core abstractions)
1. `PKGBUILDEditor` - 61 edges
2. `PackageService` - 48 edges
3. `AppConfig` - 37 edges
4. `BaseParser` - 34 edges
5. `RuleParser` - 33 edges
6. `ApiParser` - 32 edges
7. `PackageUpdater` - 30 edges
8. `make_app_config()` - 30 edges
9. `TraeParser` - 26 edges
10. `_service()` - 26 edges

## Surprising Connections (you probably didn't know these)
- `B12【注释/文档同步】（过时注释比没有注释更误导）` --references--> `lifespan()`  [INFERRED]
  docs/code-review-2026-10-10.md → projects/aur-metadata/src/aur_metadata/cli.py
- `B4【中·行为】QQ 查询路径对上游无节流、无复用` --references--> `QQParser`  [INFERRED]
  docs/code-review-2026-10-10.md → projects/aur-metadata/src/aur_metadata/parsers/qq.py
- `A3【高·安全】三条注入面：aria2c input-file 注入 / 下载文件名路径穿越 / PKGBUILD 换行注入` --references--> `generate_download_filename()`  [INFERRED]
  docs/code-review-2026-10-10.md → projects/aur-auto-update/src/aur_auto_update/utils/url_utils.py
- `四、分析后不修的项（附理由）` --references--> `compare_versions()`  [INFERRED]
  docs/code-review-2026-10-10.md → projects/aur-auto-update/src/aur_auto_update/utils/version_utils.py
- `第 3 步：配置 updater` --references--> `pkgbuild()`  [INFERRED]
  docs/adding-a-package.md → projects/aur-auto-update/tests/test_pkgbuild_editor.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **B2 hash support implementation flow (Enum → Config → Updater)** — specs_hash_algorithm_enum, specs_blake2b_builder, specs_hash_algorithm_field, specs_pkgbuild_editor_api, specs_package_updater_hardcode_removal [EXTRACTED 0.95]
- **Update → SRCINFO → Commit → AUR Push Pipeline** — github_workflows_update_packages, wf_arch_pkg_action, wf_aur_deploy_action, rules_srcinfo [INFERRED 0.85]
- **makepkg checksum / cache-busting rule cluster** — rules_source_alias_cache, rules_carch_in_source, rules_local_source_hash, rules_rolling_release_checksum, tool_makepkg [INFERRED 0.85]

## Communities (160 total, 82 thin omitted)

### Community 0 - "test_package_seeder.py"
Cohesion: 0.06
Nodes (27): build_tortoise_config(), close_db(), get_db_url(), init_db(), _load_schema_sql(), _split_sql(), PackageHash, Meta (+19 more)

### Community 1 - "PKGBUILDEditor"
Cohesion: 0.06
Nodes (7): A3【高·安全】三条注入面：aria2c input-file 注入 / 下载文件名路径穿越 / PKGBUILD 换行注入, PKGBUILDEditor, TestPKGBUILDEditorEdgeCases, TestPKGBUILDEditorGetters, TestPKGBUILDEditorUpdate, TestUpdateSourceArchEdgeCases, TestUpdateSourceEdgeCases

### Community 3 - "test_schedule_service.py"
Cohesion: 0.12
Nodes (18): _build_service(), _cfg(), FakeScheduler, _pkg(), _svc(), test_build_trigger_cron(), test_build_trigger_cron_missing_expr_raises(), test_build_trigger_interval_deferred_has_future_start() (+10 more)

### Community 4 - "get_package"
Cohesion: 0.14
Nodes (6): get_package(), list_packages(), reload_packages(), ApiResponse, success(), test_success_envelope()

### Community 7 - "package_service.py"
Cohesion: 0.15
Nodes (5): ArchEnum, HashAlgorithmEnum, BaseParser, PackageFileVersionParser, ZenParser

### Community 8 - "AUR 打包实践指南"
Cohesion: 0.13
Nodes (15): AUR 打包实践指南, license [官方规范], pkgdesc [官方规范], provides 和 conflicts [推荐实践], Shell 补全 [推荐实践], source 声明 [推荐实践], .SRCINFO [官方规范], 代码质量 [推荐实践] (+7 more)

### Community 9 - "PackageUpdater"
Cohesion: 0.13
Nodes (5): A1【高·行为】无效包名 / 部分失败时进程退出码为 0, 四、分析后不修的项（附理由）, _dispatch(), PackageUpdater, UpdateSummary

### Community 10 - "ApiParser"
Cohesion: 0.08
Nodes (6): ApiParser, TestApiParseDownloadUrls, TestApiParseHashes, TestApiParseSuccess, TestApiParseUrls, TestApiParseVersionFailures

### Community 11 - "json"
Cohesion: 0.11
Nodes (19): TraeParser, test_rule_deb_parser_version_rule_not_required(), _entry(), _payload(), test_default_region_is_cn(), test_parse_url_download_not_list(), test_parse_url_each_arch(), test_parse_url_region_not_present() (+11 more)

### Community 12 - "test_package_service.py"
Cohesion: 0.10
Nodes (21): _service(), test_collect_always_redownloads_hash(), test_collect_computes_all_algorithms(), test_collect_now_info_has_empty_download_urls(), test_collect_now_throttled(), test_collect_success_persists_version_and_hashes(), test_collect_version_fetch_failure_records_and_raises(), test_collect_version_survives_full_hash_failure() (+13 more)

### Community 13 - "AGENTS.md"
Cohesion: 0.29
Nodes (6): Commit 规范, graphify, 开发命令, 注意事项, 添加新软件包, 项目结构（uv workspace monorepo）

### Community 14 - "packages.py"
Cohesion: 0.13
Nodes (5): get_package_service(), get_schedule_service(), SchedulerConfig, BizError, ScheduleService

### Community 15 - "设计"
Cohesion: 0.15
Nodes (12): 1. HashAlgorithmEnum 新增 B2, 2. 注册 blake2b 构建器, 3. 配置模型新增 hash_algorithm 字段, 4. config.yaml 配置, 5. PKGBUILDEditor API 清理, 6. PackageUpdater 消除硬编码, 7. 单元测试补充, B2 (BLAKE2b) 哈希算法支持设计 (+4 more)

### Community 16 - "get_parser"
Cohesion: 0.10
Nodes (13): get_parser(), test_get_parser_deb_with_urls_config(), test_get_parser_empty_config_is_no_arg(), test_get_parser_returns_new_instance(), test_get_parser_rule_deb_needs_no_version_config(), test_get_parser_rule_invalid_config_raises(), test_get_parser_rule_requires_version_config(), test_get_parser_rule_with_rules_config() (+5 more)

### Community 18 - "Fetcher"
Cohesion: 0.11
Nodes (11): Fetcher, _response(), test_extract_message_from_error_body(), test_fetch_text_network_error_retried(), test_fetch_text_no_retry_when_max_retries_zero(), test_fetch_text_permanent_error_no_retry(), test_fetch_text_retryable_exhausted(), test_fetch_text_retryable_then_success() (+3 more)

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
Cohesion: 0.20
Nodes (8): _FakeDownloader, _parsed(), test_get_checksums_complete_hashes_skip_download(), test_get_checksums_falls_back_to_urls(), test_get_checksums_no_url_skips_arch(), test_get_checksums_partial_arch_without_url_fails(), test_get_checksums_prefers_download_urls(), _updater()

### Community 40 - "zen-browser-twilight.sh"
Cohesion: 0.50
Nodes (3): MOZ_APP_LAUNCHER, zen-browser-twilight.sh script, ZEN_USER_FLAGS

### Community 41 - "test_base_parser.py"
Cohesion: 0.08
Nodes (14): _Concrete, test_arch_value_from_enum(), test_arch_value_from_string(), test_cache_bad_json_not_reparsed(), test_cache_hits_same_response_object(), test_cache_invalidates_on_new_response(), test_invalid_json_logged_as_structure_change(), test_log_structure_change_format() (+6 more)

### Community 44 - "test_rule_parser.py"
Cohesion: 0.11
Nodes (25): RuleParser, _rule(), _static_urls(), _structure_changed(), test_css_selector(), test_first_false_joins_all_hits(), test_invalid_rule_raises(), test_invalid_url_rule_raises() (+17 more)

### Community 47 - "AUR 包已知问题"
Cohesion: 0.22
Nodes (9): AUR 包已知问题, makepkg 缓存冲突, Navicat（navicat17-premium-zh-cn）, tarball 内包含冗余文件, Trae 系列（trae / trae-sg / trae-us / trae-cn）, 修改本地源文件后 hash 不匹配, 捆绑 GCC 运行时库导致 ckg 索引崩溃, 捆绑 libsystemd 与系统 libmount 不兼容 (+1 more)

### Community 49 - "Update Packages Workflow"
Cohesion: 0.48
Nodes (5): Conventional Commits Standard, Push to AUR Workflow, Update Packages Workflow, awsl1414/archlinux-package-action, github-actions-deploy-aur Action

### Community 53 - "trae"
Cohesion: 0.50
Nodes (3): Feedback, Install, trae

### Community 54 - "aur-metadata/AGENTS.md"
Cohesion: 0.40
Nodes (3): 开发命令, 目录结构, 项目定位

### Community 59 - "linuxqq-nt"
Cohesion: 0.50
Nodes (3): Feedback, Install, linuxqq-nt

### Community 62 - "zen-browser-twilight-bin"
Cohesion: 0.50
Nodes (3): Feedback, Install, zen-browser-twilight-bin

### Community 63 - "test_api_packages.py"
Cohesion: 0.18
Nodes (15): refresh_package(), ErrorCode, _info(), _svc_pkg(), _svc_refresh(), _svc_sched(), test_get_package_data_not_ready(), test_get_package_not_found() (+7 more)

### Community 65 - "generate_download_filename"
Cohesion: 0.13
Nodes (7): extract_extension_from_url(), extract_filename_from_url(), generate_download_filename(), _sanitize_component(), TestExtractExtensionFromUrl, TestExtractFilenameFromUrl, TestGenerateDownloadFilename

### Community 80 - "AppConfig"
Cohesion: 0.14
Nodes (3): AppConfig, QQParser, RuleDebParser

### Community 81 - "response.py"
Cohesion: 0.10
Nodes (14): _envelope(), register_exception_handlers(), _handle_biz_error(), _handle_unhandled(), _handle_validation_error(), _client_with(), endpoint(), test_api_response_generic_roundtrip() (+6 more)

### Community 82 - "test_app_integration.py"
Cohesion: 0.22
Nodes (4): _config(), _package(), test_lifespan_assembles_services_and_seeds(), test_openapi_version_from_package_metadata()

### Community 83 - "Fetcher"
Cohesion: 0.12
Nodes (8): _run(), _describe_http_error(), Fetcher, _download_one(), _attempt(), _attempt(), _is_retryable(), _with_github_auth()

### Community 84 - "API 路由文档"
Cohesion: 0.17
Nodes (7): API 路由文档, 列出所有已注册包, 定时采集与数据库, 手动触发采集并落库, 查询指定包的最新版本与文件 hash, 路由, 重新加载包配置并同步调度

### Community 85 - "test_qq_parser.py"
Cohesion: 0.06
Nodes (13): _make_downloader(), TestBuildBaseArgs, TestUrlSafety, _payload(), test_parse_url_accepts_string_arch(), test_parse_url_loongarch_as_plain_string(), test_parse_url_missing_arm_field(), test_parse_url_non_str_deb_value() (+5 more)

### Community 86 - "PackageConfig"
Cohesion: 0.14
Nodes (3): PackageConfig, TestPackageConfig, TestPackageConfigUnknownArch

### Community 87 - "compare_versions"
Cohesion: 0.17
Nodes (4): compare_versions(), parse_version(), TestCompareVersions, TestParseVersion

### Community 89 - "_make_fetcher"
Cohesion: 0.15
Nodes (8): _make_fetcher(), counting_handler(), test_no_retry_on_client_error_status(), test_retry_exhausted_on_read_timeout_stream(), test_retry_exhausted_returns_none(), test_retry_on_503_then_success(), test_retry_transient_then_success(), handler()

### Community 90 - "test_zen_parser.py"
Cohesion: 0.14
Nodes (11): _payload(), test_parse_url_accepts_string_arch(), test_parse_url_asset_without_download_url(), test_parse_url_each_arch(), test_parse_url_empty_assets(), test_parse_url_no_matching_asset(), test_parse_url_null_assets(), test_parse_url_unsupported_arch() (+3 more)

### Community 92 - "load_config"
Cohesion: 0.26
Nodes (8): load_config(), test_default_from_member_dir(), test_default_from_repo_root(), test_default_missing_lists_candidates(), test_env_var_beats_default(), test_explicit_arg_beats_env(), test_load_packages_default_from_repo_root(), _write()

### Community 93 - "二、aur-metadata 修复清单"
Cohesion: 0.13
Nodes (11): B10【低·依赖】`jmespath` 未声明直接依赖, B11【低·整洁】删除未使用索引与 `__future__` 导入, B12【注释/文档同步】（过时注释比没有注释更误导）, B2【中·行为】`ScheduleService._collect` 宽 except 把一切异常误标为“包不存在”, B3【中·设计】手动 refresh 被无谓耦合到“调度器已启用”, B4【中·行为】QQ 查询路径对上游无节流、无复用, B5【中·一致性】逐架构 URL 提取循环两处逐字重复, B6【低·行为】CPU 密集的 deb 头部解压阻塞事件循环 (+3 more)

### Community 103 - "test_fetcher_head.py"
Cohesion: 0.20
Nodes (8): _make_fetcher(), counting_handler(), test_fetch_head_404_returns_none(), test_fetch_head_invalid_max_bytes_raises(), test_fetch_head_reads_prefix_and_sends_range(), handler(), test_fetch_head_retry_transient_then_success(), test_fetch_head_short_body_returns_all()

### Community 106 - "CollectThrottledError"
Cohesion: 0.33
Nodes (3): CollectThrottledError, test_collect_now_concurrent_second_is_throttled(), test_collect_now_throttled()

### Community 107 - "downloader.py"
Cohesion: 0.15
Nodes (3): A8【低·死代码】无调用方的参数/字段/冗余捕获, Downloader, DownloadResult

### Community 108 - "PackageRegistry"
Cohesion: 0.17
Nodes (7): PackageRegistry, _entry(), test_entry_holds_parser_instance(), test_entry_is_frozen(), test_get_hit_and_miss(), test_list_all_returns_copy(), test_replace_all_rebuilds_from_scratch()

### Community 112 - "conftest.py"
Cohesion: 0.09
Nodes (9): get_hash_builder(), _Hash, _clean_config_env(), db(), make_package(), qq_response(), test_get_hash_builder_case_insensitive(), test_get_hash_builder_known_algorithms() (+1 more)

### Community 113 - "三、仓库根资产清单"
Cohesion: 0.15
Nodes (12): C1【高·决策项，仅报告】`packages/ruzu-appimage/` 半注册真空, C2【中·决策项，仅报告】`bt-dualboot-ng` Maintainer 头与其余 9 包不一致（邮箱不同）——需用户确认正确身份后统一。, C3【低·执行】`zen-browser-twilight-bin` pkgdesc 单引号为全仓唯一异类 → 统一双引号。, C4【低·决策项，仅报告】`z-code` source URL 文件名粒度低于 pkgver（缺 build 号）——建议补 `${pkgver}-${pkgrel}` 别名，但需 makepkg 实际构建验证，不盲改。, C5【低·执行】`docs/adding-a-package.md` 补 CI 行为警示（packages/ 下建目录即会被 push-to-aur 扫描发布）。, C6【低·决策项，仅报告】`docs/superpowers/specs/2026-06-01-b2-hash-support-design.md` 为无引用孤儿文档（主题已落地），去留由用户定。, C7【低·记录】根 `config.yaml` `ignore_ssl_errors: true` 削弱“API 拉哈希写 PKGBUILD”信任链——属用户环境选择（注释已警示），不代改，仅记录建议生产置 false。, 三、仓库根资产清单 (+4 more)

### Community 114 - "load_packages"
Cohesion: 0.23
Nodes (11): load_packages(), _resolve_path(), test_load_allows_explicit_empty_packages(), test_load_cron_schedule(), test_load_default_packages_file(), test_load_parses_fields_with_defaults(), test_load_rejects_bad_field_types(), test_load_rejects_duplicate_name_and_unknown_key() (+3 more)

### Community 115 - "make_app_config"
Cohesion: 0.20
Nodes (7): 注意事项, DatabaseConfig, GithubConfig, HttpConfig, QQConfig, ServerConfig, make_app_config()

### Community 118 - "DebParser"
Cohesion: 0.12
Nodes (9): DebControlVersionMixin, DebParser, test_get_parser_deb_with_config(), test_parse_url_from_config(), test_parse_url_unknown_arch_warns_and_none(), test_parse_version_always_none(), test_urls_canonical_keys_passthrough(), test_urls_deb_arch_aliases_normalized() (+1 more)

### Community 119 - "PackageService"
Cohesion: 0.09
Nodes (5): B8【低·整理】`asyncio.Lock()` 急切构造 + 死代码清除, DataNotReadyError, PackageNotFoundError, PackageService, _utcnow()

### Community 120 - "ConfigLoader"
Cohesion: 0.20
Nodes (5): A9【中·一致性】日志与命名风格统一, ApiSettings, ConfigLoader, DownloadSettings, TestHashAlgorithmValidation

### Community 121 - "rule.py"
Cohesion: 0.19
Nodes (4): _build_rule(), ExtractRule, _sorted_kinds(), _validate_expr_syntax()

### Community 124 - "FakeFetcher"
Cohesion: 0.14
Nodes (3): FakeFetcher, test_get_info_pure_read_no_fetch(), test_get_info_urls_aligns_with_current_archs()

### Community 125 - "一、aur-auto-update 修复清单"
Cohesion: 0.29
Nodes (7): A10【中·组织】文件组织与 aur-metadata 对齐（目标布局：config.py / fetcher.py / services/ / parsers/ / utils/ / constants/ + 扁平 tests/）, A2【高·行为】部分架构拿不到校验和时静默“成功”，PKGBUILD 带旧校验和升版本, A4【中·行为】`hash_algorithm` 配置无校验，配错算法静默半更新, A5【中·行为】`asyncio.gather(return_exceptions=True)` 吞掉取消信号, A6【中·兼容代码】`--all/-a` 是死参数, A7【中·兼容代码】编辑器死 API：epoch 方法与“静默自动保存”上下文管理器, 一、aur-auto-update 修复清单

### Community 127 - "_zcode_parser"
Cohesion: 0.29
Nodes (4): test_zcode_url_rule_fails_on_renamed_artifact(), test_zcode_url_rules_extract_both_archs(), test_zcode_version_from_package_head(), _zcode_parser()

### Community 129 - "AUR 包自动更新工具"
Cohesion: 0.25
Nodes (8): AUR 包自动更新工具, 开发, 快速开始, 技术栈, 支持的包, 特性, 许可证, 贡献

### Community 130 - "注释规范"
Cohesion: 0.33
Nodes (5): 注释规范, 示例, 自检, 规则, 风格细节

### Community 133 - "贡献指南"
Cohesion: 0.40
Nodes (5): Commit 规范, 分支策略, 提交流程, 添加新软件包, 贡献指南

### Community 134 - "PackageInfo"
Cohesion: 0.15
Nodes (7): `PackageInfo`, `PackageList`, 数据模型, PackageInfo, PackageList, FakePackageService, FakeScheduleService

### Community 135 - "pytest"
Cohesion: 0.05
Nodes (31): DebParseError, normalize_deb_version(), parse_deb_control_version(), _version_from_control_tar(), build_deb(), test_version_from_package_head_success(), test_normalize_deb_version(), test_parse_accepts_trailing_bytes() (+23 more)

### Community 136 - "z-code"
Cohesion: 0.50
Nodes (3): Feedback, Install, z-code

### Community 159 - "aur_metadata/cli.py"
Cohesion: 0.14
Nodes (8): _app_version(), _configure_logging(), create_app(), _debug_extract(), lifespan(), main(), PackageConfig, _definition_fields()

### Community 160 - "添加新软件包"
Cohesion: 0.17
Nodes (10): 添加新软件包, 第 1 步：编写 PKGBUILD, 第 2 步：注册元数据采集, 第 3 步：配置 updater, 验证, aur-auto-update, 使用, 前置依赖 (+2 more)

### Community 161 - "aur-metadata"
Cohesion: 0.25
Nodes (8): aur-metadata, Docker 部署, 使用, 开发, 技术栈, 数据持久化, 简介, 配置文件

### Community 169 - "统一响应结构"
Cohesion: 0.50
Nodes (4): 业务码, 成功响应, 统一响应结构, 错误响应

## Knowledge Gaps
- **40 isolated node(s):** `QQ_DEFAULT_FLAGS`, `QQ_USER_FLAGS`, `LD_PRELOAD`, `TRAE_USER_FLAGS`, `TRAE_USER_FLAGS` (+35 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 769 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **82 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PackageService` connect `PackageService` to `test_schedule_service.py`, `PackageInfo`, `package_service.py`, `pytest`, `.collect_hashes`, `PackageRegistry`, `test_package_service.py`, `packages.py`, `test_api_packages.py`, `Fetcher`, `PackageEntry`, `FakeFetcher`, `二、aur-metadata 修复清单`, `aur_metadata/cli.py`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `PKGBUILDEditor` (e.g. with `PackageUpdater` and `TestPKGBUILDEditorEdgeCases`) actually correct?**
  _`PKGBUILDEditor` has 6 INFERRED edges - model-reasoned connections that need verification._
- **What connects `QQ_DEFAULT_FLAGS`, `QQ_USER_FLAGS`, `LD_PRELOAD` to the rest of the system?**
  _40 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_package_seeder.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06140350877192982 - nodes in this community are weakly interconnected._
- **Why does `pkgbuild()` connect `添加新软件包` to `PKGBUILDEditor`, `package_updater.py`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Are the 18 inferred relationships involving `PackageService` (e.g. with `get_package_service()` and `lifespan()`) actually correct?**
  _`PackageService` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Should `PKGBUILDEditor` be split into smaller, more focused modules?**
  _Cohesion score 0.05636114911080711 - nodes in this community are weakly interconnected._