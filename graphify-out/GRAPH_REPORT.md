# Graph Report - .  (2026-06-25)

## Corpus Check
- Corpus is ~11,875 words - fits in a single context window. You may not need a graph.

## Summary
- 450 nodes · 795 edges · 39 communities (29 shown, 10 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 102 edges (avg confidence: 0.6)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 38|Community 38]]

## God Nodes (most connected - your core abstractions)
1. `PKGBUILDEditor` - 52 edges
2. `ArchEnum` - 35 edges
3. `PackageUpdater` - 32 edges
4. `QQParser` - 22 edges
5. `PackageConfig` - 21 edges
6. `BaseParser` - 21 edges
7. `TraeParser` - 21 edges
8. `NavicatPremiumCSParser` - 19 edges
9. `calculate_file_hash()` - 15 edges
10. `HashAlgorithmEnum` - 14 edges

## Surprising Connections (you probably didn't know these)
- `trae Package (China CDN)` --references--> `Trae Bundled GCC Runtime ABI Conflict`  [INFERRED]
  README.md → docs/troubleshooting.md
- `trae-sg Package (Singapore CDN)` --references--> `Trae Bundled GCC Runtime ABI Conflict`  [INFERRED]
  README.md → docs/troubleshooting.md
- `trae-us Package (US CDN)` --references--> `Trae Bundled GCC Runtime ABI Conflict`  [INFERRED]
  README.md → docs/troubleshooting.md
- `trae-cn Package (Domestic)` --references--> `Trae Bundled GCC Runtime ABI Conflict`  [INFERRED]
  README.md → docs/troubleshooting.md
- `CLAUDE.md Project Instructions` --references--> `Type Annotation Rules`  [EXTRACTED]
  CLAUDE.md → .claude/rules/type-hints.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Trae variant packages share makepkg cache + GCC lib issues** — pkg_trae, pkg_trae_sg, pkg_trae_us, pkg_trae_cn, issue_trae_makepkg_cache, issue_trae_gcc_libs [INFERRED 0.85]
- **Update → SRCINFO → Commit → AUR Push Pipeline** — workflows_update_packages, wf_arch_pkg_action, wf_aur_deploy_action, rules_srcinfo [INFERRED 0.85]
- **makepkg checksum / cache-busting rule cluster** — rules_source_alias_cache, rules_carch_in_source, rules_local_source_hash, rules_rolling_release_checksum, tool_makepkg [INFERRED 0.85]
- **B2 hash support implementation flow (Enum → Config → Updater)** — specs_hash_algorithm_enum, specs_blake2b_builder, specs_hash_algorithm_field, specs_pkgbuild_editor_api, specs_package_updater_hardcode_removal [EXTRACTED 0.95]
- **Trae CDN variant package family (CN/SG/US share API + version)** — config_yaml_trae_pkg, config_yaml_trae_sg_pkg, config_yaml_trae_us_pkg, config_yaml_trae_cn_pkg, packages_trae_bytedance_ide [INFERRED 0.85]
- **Package update pipeline (config → PackageUpdater → PKGBUILD)** — scripts_config_yaml, scripts_package_updater_module, specs_pkgbuild_editor_api, config_yaml_settings_hash_algorithm [INFERRED 0.85]

## Communities (39 total, 10 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (18): BaseException, HashAlgorithmEnum, PKGBUILDEditor, PKGBUILD 文件编辑器，支持上下文管理器自动保存, 更新非架构特定的 source URL（用于 arch=('any') 包），保留已有的 :: 别名, 更新非架构特定的校验和字段（用于 arch=('any') 包）, 更新特定架构的 source URL，保留已有的 :: 别名, pkgbuild() (+10 more)

### Community 1 - "Community 1"
Cohesion: 0.11
Nodes (13): ABC, ParserEnum, 包更新器 整合fetch、parse和update三个流程  架构设计： 1. 并行更新所有维护的 AUR 包（使用 asyncio.gather） 2. 并行, Enum, BaseParser, 解析器抽象基类，定义版本号和 URL 解析接口, Navicat Premium 版本解析器, NavicatPremiumCSParser 单元测试 (+5 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (39): CLAUDE.md Project Instructions, CONTRIBUTING Guide, README - AUR Package Auto-Updater, Dev-Main Branch Strategy, BaseParser Plugin Pattern, Conventional Commits Standard, AUR Packaging Practice Guide, AUR Known Issues / Troubleshooting (+31 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (14): Any, ArchEnum, PyPIParser, PyPI 包解析器      从 PyPI JSON API 获取包的最新版本和 sdist 下载 URL。      API 端点: https://pypi, 从 PyPI JSON 响应中提取 sdist 下载 URL          对于 arch='any' 的纯 Python 包，返回 sdist URL。, QQParser, 从 JavaScript 响应中提取并解析 JSON 配置, 从已解析的 JSON 中获取指定架构的 deb 下载 URL (+6 more)

### Community 4 - "Community 4"
Cohesion: 0.09
Nodes (17): BaseModel, ConfigLoader, DownloadSettings, PackageConfig, 将字符串架构列表转换为 ArchEnum 列表, 获取生效的哈希算法（包级覆盖 > 全局默认）, Settings, 全局默认 hash_algorithm 为 b2 (+9 more)

### Community 5 - "Community 5"
Cohesion: 0.13
Nodes (14): Path, Protocol, calculate_file_hash(), calculate_multiple_hashes(), _Hash, 计算文件哈希值      支持 SHA256 和 SHA512 算法，分块读取大文件避免内存占用过高, 一次性计算文件的多种哈希值，只读取文件一次, verify_file_hash() (+6 more)

### Community 6 - "Community 6"
Cohesion: 0.09
Nodes (31): bt-dualboot-ng package config (PyPIParser), navicat package config (NavicatPremiumCSParser), qq package config (QQParser), settings.hash_algorithm (global default = b2), trae-cn package config (TraeParser_CN, independent product), trae package config (TraeParser), trae-sg package config (TraeParser_SG), trae-us package config (TraeParser_US) (+23 more)

### Community 7 - "Community 7"
Cohesion: 0.10
Nodes (11): _make_zen_response(), 构造 Zen GitHub Release JSON 响应, ZenParser.parse_version 测试, 正常从 release name 提取版本号, ZenParser.parse_url 测试, 不支持的架构（loong64）返回 None, TestZenParseUrl, TestZenParseVersion (+3 more)

### Community 8 - "Community 8"
Cohesion: 0.13
Nodes (11): PackageUpdater, 检查 PKGBUILD 文件是否存在          Args:             package_name: 包名             packa, 下载文件并计算校验和          使用 Downloader 的并发下载功能，并行下载单个包的所有架构, 处理版本不更新的情况（当前版本 >= 新版本）          两种场景：         1. 当前版本 > 新版本：版本降级，仅验证哈希, 包更新器，整合fetch、parse和update流程, 并行更新所有配置的包          所有包同时进入更新流程，每个包的多个架构并行下载          Returns:             (成功数量, 检查包是否可更新          Args:             package_name: 包名             package_config:, 更新指定的包列表          Args:             package_names: 包名列表          Returns: (+3 more)

### Community 9 - "Community 9"
Cohesion: 0.14
Nodes (9): TestExtractExtensionFromUrl, TestExtractFilenameFromUrl, TestGenerateDownloadFilename, extract_extension_from_url(), extract_filename_from_url(), generate_download_filename(), 从 URL 中提取文件扩展名（包含点号）      支持复合扩展名（如 .tar.gz）和普通扩展名, 生成标准化的下载文件名      格式: {package_name}_{version}_{arch}{extension}     自动从 URL 提取扩展 (+1 more)

### Community 10 - "Community 10"
Cohesion: 0.17
Nodes (6): TestCompareVersions, TestParseVersion, compare_versions(), parse_version(), 比较两个版本号      Args:         version1: 第一个版本号         version2: 第二个版本号      Return, 解析版本号为可比较的组成部分      Args:         version: 版本字符串，如 "3.2.22_251203", "17.3.5"

### Community 11 - "Community 11"
Cohesion: 0.23
Nodes (4): NavicatPremiumCSParser, Navicat Premium CS 版本解析器, TestNavicatParseUrl, TestNavicatParseVersion

### Community 12 - "Community 12"
Cohesion: 0.29
Nodes (5): Fetcher, test_fetch_json_failure(), test_fetch_json_success(), test_fetch_text_failure(), test_fetch_text_success()

### Community 13 - "Community 13"
Cohesion: 0.32
Nodes (4): Downloader, DownloadResult, 基于 aria2c 的异步下载器      特性：     - 多连接分片下载（aria2c -x/-s）     - 断点续传（aria2c -c）, 使用单个 aria2c 实例批量下载多个文件          Args:             downloads: {arch: (url, file_p

### Community 14 - "Community 14"
Cohesion: 0.39
Nodes (3): format_checksum_for_pkgbuild(), format_checksum_for_pkgbuild 测试, TestFormatChecksumForPkgbuild

### Community 15 - "Community 15"
Cohesion: 0.50
Nodes (3): zen-browser-twilight.sh script, MOZ_APP_LAUNCHER, ZEN_USER_FLAGS

## Knowledge Gaps
- **33 isolated node(s):** `linuxqq.sh script`, `QQ_USER_FLAGS`, `navicat.sh script`, `LD_PRELOAD`, `trae-cn.sh script` (+28 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PackageUpdater` connect `Community 8` to `Community 0`, `Community 1`, `Community 3`, `Community 4`, `Community 7`, `Community 11`, `Community 12`, `Community 13`?**
  _High betweenness centrality (0.189) - this node is a cross-community bridge._
- **Why does `PKGBUILDEditor` connect `Community 0` to `Community 8`, `Community 1`?**
  _High betweenness centrality (0.144) - this node is a cross-community bridge._
- **Why does `ArchEnum` connect `Community 3` to `Community 1`, `Community 4`, `Community 7`, `Community 8`, `Community 11`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `PKGBUILDEditor` (e.g. with `PackageUpdater` and `HashAlgorithmEnum`) actually correct?**
  _`PKGBUILDEditor` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `ArchEnum` (e.g. with `PackageUpdater` and `ConfigLoader`) actually correct?**
  _`ArchEnum` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `PackageUpdater` (e.g. with `ArchEnum` and `HashAlgorithmEnum`) actually correct?**
  _`PackageUpdater` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `QQParser` (e.g. with `PackageUpdater` and `ArchEnum`) actually correct?**
  _`QQParser` has 5 INFERRED edges - model-reasoned connections that need verification._