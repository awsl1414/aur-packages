# Graph Report - aur-packages  (2026-06-26)

## Corpus Check
- 67 files · ~13,755 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 594 nodes · 973 edges · 63 communities (51 shown, 12 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 107 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `36ee0871`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

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
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]

## God Nodes (most connected - your core abstractions)
1. `PKGBUILDEditor` - 73 edges
2. `ArchEnum` - 36 edges
3. `PackageUpdater` - 33 edges
4. `PackageConfig` - 23 edges
5. `BaseParser` - 22 edges
6. `QQParser` - 22 edges
7. `TraeParser` - 22 edges
8. `NavicatPremiumCSParser` - 19 edges
9. `AUR 打包实践指南` - 19 edges
10. `TestUpdateSourceArchEdgeCases` - 18 edges

## Surprising Connections (you probably didn't know these)
- `trae Package (China CDN)` --references--> `Trae Bundled GCC Runtime ABI Conflict`  [INFERRED]
  README.md → docs/troubleshooting.md
- `trae-sg Package (Singapore CDN)` --references--> `Trae Bundled GCC Runtime ABI Conflict`  [INFERRED]
  README.md → docs/troubleshooting.md
- `trae-us Package (US CDN)` --references--> `Trae Bundled GCC Runtime ABI Conflict`  [INFERRED]
  README.md → docs/troubleshooting.md
- `trae-cn Package (Domestic)` --references--> `Trae Bundled GCC Runtime ABI Conflict`  [INFERRED]
  README.md → docs/troubleshooting.md
- `trae package config (TraeParser)` --references--> `Trae AI IDE by ByteDance (CDN variants)`  [INFERRED]
  scripts/config.yaml → packages/trae/README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Trae variant packages share makepkg cache + GCC lib issues** — pkg_trae, pkg_trae_sg, pkg_trae_us, pkg_trae_cn, issue_trae_makepkg_cache, issue_trae_gcc_libs [INFERRED 0.85]
- **Update → SRCINFO → Commit → AUR Push Pipeline** — workflows_update_packages, wf_arch_pkg_action, wf_aur_deploy_action, rules_srcinfo [INFERRED 0.85]
- **makepkg checksum / cache-busting rule cluster** — rules_source_alias_cache, rules_carch_in_source, rules_local_source_hash, rules_rolling_release_checksum, tool_makepkg [INFERRED 0.85]
- **B2 hash support implementation flow (Enum → Config → Updater)** — specs_hash_algorithm_enum, specs_blake2b_builder, specs_hash_algorithm_field, specs_pkgbuild_editor_api, specs_package_updater_hardcode_removal [EXTRACTED 0.95]
- **Trae CDN variant package family (CN/SG/US share API + version)** — config_yaml_trae_pkg, config_yaml_trae_sg_pkg, config_yaml_trae_us_pkg, config_yaml_trae_cn_pkg, packages_trae_bytedance_ide [INFERRED 0.85]
- **Package update pipeline (config → PackageUpdater → PKGBUILD)** — scripts_config_yaml, scripts_package_updater_module, specs_pkgbuild_editor_api, config_yaml_settings_hash_algorithm [INFERRED 0.85]

## Communities (63 total, 12 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.14
Nodes (4): 更新校验和字段。          arch=None 更新非架构特定 sums=()（arch=('any') 包），否则更新 sums_<arch>=()。, 替换 ^field=.*$ 整行为 field=value（MULTILINE）。字段不存在时无操作。          用 lambda 返回替换文本，避免, 返回 ^field=(.*)$ 的捕获值；字段不存在返回 None。, 取标量并按 int 解析；缺失或解析失败返回 default。

### Community 1 - "Community 1"
Cohesion: 0.11
Nodes (13): ABC, ParserEnum, 包更新器 整合fetch、parse和update三个流程  架构设计： 1. 并行更新所有维护的 AUR 包（使用 asyncio.gather） 2. 并行, Enum, BaseParser, 解析器抽象基类，定义版本号和 URL 解析接口, Navicat Premium 版本解析器, NavicatPremiumCSParser 单元测试 (+5 more)

### Community 2 - "Community 2"
Cohesion: 0.18
Nodes (11): AppImage Dependency Analysis Practice, No ${CARCH} in source_<arch> Rule, Electron SUID Sandbox Practice, Launcher Script Path Coupling Risk, Local Source Hash Sync Rule, pkgrel Revision Rule, pkgver Versioning Rule, Rolling Release Source Checksum Rule (+3 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (13): Any, PyPIParser, PyPI 包解析器      从 PyPI JSON API 获取包的最新版本和 sdist 下载 URL。      API 端点: https://pypi, 从 PyPI JSON 响应中提取 sdist 下载 URL          对于 arch='any' 的纯 Python 包，返回 sdist URL。, QQParser, 从 JavaScript 响应中提取并解析 JSON 配置, 从已解析的 JSON 中获取指定架构的 deb 下载 URL, 从 QQ 响应数据中提取版本号（含构建号），并交叉验证 API 与 URL 版本 (+5 more)

### Community 4 - "Community 4"
Cohesion: 0.07
Nodes (26): BaseModel, ArchEnum, HashAlgorithmEnum, PackageUpdater, 检查 PKGBUILD 文件是否存在          Args:             package_name: 包名             packa, 下载文件并计算校验和          使用 Downloader 的并发下载功能，并行下载单个包的所有架构, 处理版本不更新的情况（当前版本 >= 新版本）          两种场景：         1. 当前版本 > 新版本：版本降级，仅验证哈希, 包更新器，整合fetch、parse和update流程 (+18 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (19): Path, 更新 source URL 时保留 :: 别名, update_source（arch 特定）替换逻辑的边界条件测试, URL 含 ${_gh}（花括号）时保留 shell 变量，不更新, URL 含 $_gh（无花括号）时同样应保留，等价于 ${_gh}, 别名含 ${pkgver}、URL 硬编码时，保留别名、替换 URL, 单行多条目：替换远程 URL，保留本地源文件, 缺失 source_<arch> 字段时不破坏其它内容 (+11 more)

### Community 6 - "Community 6"
Cohesion: 0.28
Nodes (8): settings.hash_algorithm (global default = b2), Rationale: zen-browser-twilight-bin uses b2sums but updater hardcoded SHA512, blake2b hash builder registration (_HASH_BUILDERS), get_effective_hash_algorithm method, HashAlgorithmEnum (SHA256/SHA512/B2), hash_algorithm config field (Settings + PackageConfig override), PKGBUILDEditor hash_algorithm parameterization, B2 unit tests (hash + pkgbuild_editor)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (12): _make_zen_response(), 构造 Zen GitHub Release JSON 响应, ZenParser.parse_version 测试, 正常从 release name 提取版本号, ZenParser.parse_url 测试, 不支持的架构（loong64）返回 None, TestZenParseUrl, TestZenParseVersion (+4 more)

### Community 8 - "Community 8"
Cohesion: 0.04
Nodes (45): AppImage 依赖分析 [推荐实践], AppImage 解包, AppRun 启动问题 [推荐实践], AUR 打包实践指南, deb 解包, Electron 直装（tarball）, epoch, license [官方规范] (+37 more)

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
Cohesion: 0.16
Nodes (7): Fetcher, test_fetch_text_failure(), test_fetch_text_success(), Downloader, DownloadResult, 基于 aria2c 的异步下载器      特性：     - 多连接分片下载（aria2c -x/-s）     - 断点续传（aria2c -c）, 使用单个 aria2c 实例批量下载多个文件          Args:             downloads: {arch: (url, file_p

### Community 13 - "Community 13"
Cohesion: 0.13
Nodes (13): Commit 规范, 分支策略, 提交流程, 添加新软件包, 贡献指南, AUR 包自动更新工具, 开发, 快速开始 (+5 more)

### Community 14 - "Community 14"
Cohesion: 0.29
Nodes (3): 文本是否包含 shell 变量引用（${VAR} 或 $VAR/$_VAR）, source 条目是否为远程 URL（带 :: 别名或以协议头开头）, 更新 source / source_<arch> 字段的远程 URL。          - 支持单行/多行、单条目/多条目数组；本地源条目（如 launch

### Community 15 - "Community 15"
Cohesion: 0.50
Nodes (3): zen-browser-twilight.sh script, MOZ_APP_LAUNCHER, ZEN_USER_FLAGS

### Community 39 - "Community 39"
Cohesion: 0.12
Nodes (6): BaseException, PKGBUILDEditor, PKGBUILD 文件编辑器，支持上下文管理器自动保存, PKGBUILD 中不存在该算法的校验和时返回空字符串, TestPKGBUILDEditorGetters, TestPKGBUILDEditorUpdate

### Community 40 - "Community 40"
Cohesion: 0.25
Nodes (4): update_epoch 和 get_epoch 测试, 无 epoch 行时在 pkgver 前插入, new_epoch=None 时不做任何修改, TestPKGBUILDEditorEpoch

### Community 41 - "Community 41"
Cohesion: 0.19
Nodes (7): Protocol, calculate_file_hash(), _Hash, 计算文件哈希值      支持 BLAKE2b(b2)、SHA512、SHA256 算法，分块读取大文件避免内存占用过高, calculate_file_hash 测试, 文件不存在抛出 FileNotFoundError, TestCalculateFileHash

### Community 42 - "Community 42"
Cohesion: 0.21
Nodes (6): 全局默认 hash_algorithm 为 b2, zen-browser 使用全局默认 b2（无需包级覆盖）, qq 包未设置 hash_algorithm，使用全局默认, 空 YAML 文件抛出 ValueError, 不存在的文件抛出 FileNotFoundError, TestConfigLoader

### Community 43 - "Community 43"
Cohesion: 0.17
Nodes (12): 1. HashAlgorithmEnum 新增 B2, 2. 注册 blake2b 构建器, 3. 配置模型新增 hash_algorithm 字段, 4. config.yaml 配置, 5. PKGBUILDEditor API 清理, 6. PackageUpdater 消除硬编码, 7. 单元测试补充, B2 (BLAKE2b) 哈希算法支持设计 (+4 more)

### Community 44 - "Community 44"
Cohesion: 0.20
Nodes (10): LD_PRELOAD Workaround Mechanism, Navicat Bundled libsystemd Conflict, Trae Bundled GCC Runtime ABI Conflict, Trae makepkg Cache Conflict, navicat17-premium-zh-cn Package, trae Package (China CDN), trae-cn Package (Domestic), trae-sg Package (Singapore CDN) (+2 more)

### Community 45 - "Community 45"
Cohesion: 0.28
Nodes (8): CLAUDE.md Project Instructions, CONTRIBUTING Guide, README - AUR Package Auto-Updater, Dev-Main Branch Strategy, BaseParser Plugin Pattern, aria2c Multi-threaded Downloader, ty Static Type Checker, uv Package Manager

### Community 46 - "Community 46"
Cohesion: 0.31
Nodes (9): bt-dualboot-ng package config (PyPIParser), navicat package config (NavicatPremiumCSParser), trae-cn package config (TraeParser_CN, independent product), trae package config (TraeParser), trae-sg package config (TraeParser_SG), trae-us package config (TraeParser_US), navicat17-premium-zh-cn README, navicat17-premium-zh-cn package (Chinese Simplified) (+1 more)

### Community 47 - "Community 47"
Cohesion: 0.22
Nodes (9): AUR 包已知问题, makepkg 缓存冲突, Navicat（navicat17-premium-zh-cn）, tarball 内包含冗余文件, Trae 系列（trae / trae-sg / trae-us / trae-cn）, 修改本地源文件后 hash 不匹配, 捆绑 GCC 运行时库导致 ckg 索引崩溃, 捆绑 libsystemd 与系统 libmount 不兼容 (+1 more)

### Community 48 - "Community 48"
Cohesion: 0.29
Nodes (5): PackageUpdater (Fetch → Parse → Update coordinator), scripts/, 前置依赖, 模块结构, PackageUpdater hardcoded SHA512 elimination

### Community 49 - "Community 49"
Cohesion: 0.48
Nodes (7): Conventional Commits Standard, .SRCINFO Sync Requirement, awsl1414/archlinux-package-action, github-actions-deploy-aur Action, Chinese DNS Resolution for cdn-go.cn, Push to AUR Workflow, Update Packages Workflow

### Community 50 - "Community 50"
Cohesion: 0.33
Nodes (5): Commit 规范, graphify, 开发命令, 注意事项, 添加新软件包

### Community 51 - "Community 51"
Cohesion: 0.50
Nodes (3): Feedback, Install, linuxqq-nt

### Community 52 - "Community 52"
Cohesion: 0.50
Nodes (3): Feedback, Install, navicat17-premium-zh-cn

### Community 53 - "Community 53"
Cohesion: 0.83
Nodes (4): Trae AI IDE by ByteDance (CDN variants), trae README, trae-sg README, trae-us README

### Community 54 - "Community 54"
Cohesion: 0.50
Nodes (4): 基本规则, 类型存根, 类型检查, 类型注解规范

### Community 55 - "Community 55"
Cohesion: 0.50
Nodes (3): Feedback, Install, trae

### Community 56 - "Community 56"
Cohesion: 0.50
Nodes (3): Feedback, Install, trae-sg

### Community 57 - "Community 57"
Cohesion: 0.50
Nodes (3): Feedback, Install, trae-us

### Community 58 - "Community 58"
Cohesion: 0.50
Nodes (3): Feedback, Install, zen-browser-twilight-bin

### Community 59 - "Community 59"
Cohesion: 0.67
Nodes (3): qq package config (QQParser), linuxqq-nt package (Electron QQ), linuxqq-nt README

### Community 62 - "Community 62"
Cohesion: 0.67
Nodes (3): zen-browser package config (ZenParser, twilight-1 tag), zen-browser-twilight-bin README, zen-browser-twilight-bin package (Firefox-based nightly)

## Knowledge Gaps
- **118 isolated node(s):** `linuxqq.sh script`, `QQ_USER_FLAGS`, `navicat.sh script`, `LD_PRELOAD`, `trae-cn.sh script` (+113 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PKGBUILDEditor` connect `Community 39` to `Community 0`, `Community 1`, `Community 4`, `Community 5`, `Community 40`, `Community 14`, `Community 61`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **Why does `PackageUpdater` connect `Community 4` to `Community 1`, `Community 3`, `Community 7`, `Community 39`, `Community 11`, `Community 12`?**
  _High betweenness centrality (0.117) - this node is a cross-community bridge._
- **Why does `ArchEnum` connect `Community 4` to `Community 1`, `Community 3`, `Community 7`, `Community 42`, `Community 11`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `PKGBUILDEditor` (e.g. with `PackageUpdater` and `HashAlgorithmEnum`) actually correct?**
  _`PKGBUILDEditor` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `ArchEnum` (e.g. with `PackageUpdater` and `ConfigLoader`) actually correct?**
  _`ArchEnum` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `PackageUpdater` (e.g. with `ArchEnum` and `HashAlgorithmEnum`) actually correct?**
  _`PackageUpdater` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `PackageConfig` (e.g. with `PackageUpdater` and `ArchEnum`) actually correct?**
  _`PackageConfig` has 6 INFERRED edges - model-reasoned connections that need verification._