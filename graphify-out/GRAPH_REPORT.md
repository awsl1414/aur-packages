# Graph Report - aur-packages  (2026-07-12)

## Corpus Check
- 70 files · ~17,405 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 670 nodes · 994 edges · 105 communities (55 shown, 50 thin omitted)
- Extraction: 77% EXTRACTED · 23% INFERRED · 0% AMBIGUOUS · INFERRED: 228 edges (avg confidence: 0.69)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `aecf3d98`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ArchEnum
- PackageUpdater
- AppImage Dependency Analysis Practice
- Path
- BaseParser
- ZenParser
- Rationale: zen-browser-twilight-bin uses b2sums but updater hardcoded SHA512
- QQParser
- AUR 打包实践指南
- TraeParser
- extract_extension_from_url
- compare_versions
- NavicatPremiumCSParser
- AUR 包自动更新工具
- ._update_scalar_field
- 设计
- TestPKGBUILDEditorEpoch
- ._update_source_field
- test_pkgbuild_editor.py
- 类型注解规范
- post-commit
- post-checkout
- CONTRIBUTORS List
- navicat17-premium-zh-cn
- trae-sg
- aur-auto-update
- linuxqq-nt Package
- trae-us
- zen-browser-twilight.sh
- linuxqq.sh
- navicat.sh
- trae-cn.sh
- trae.sh
- trae.sh
- trae.sh
- commit-msg
- CONTRIBUTING Guide
- README - AUR Package Auto-Updater
- Keep Repository Alive Workflow
- PKGBUILDEditor
- Dev-Main Branch Strategy
- calculate_file_hash
- BaseParser Plugin Pattern
- Navicat Bundled libsystemd Conflict
- LD_PRELOAD Workaround Mechanism
- CLAUDE.md Project Instructions
- config.yaml (global + per-package settings)
- AUR 包已知问题
- PackageUpdater (Fetch → Parse → Update coordinator)
- Update Packages Workflow
- CLAUDE.md
- Trae Bundled GCC Runtime ABI Conflict
- Trae makepkg Cache Conflict
- trae
- navicat17-premium-zh-cn Package
- trae Package (China CDN)
- trae-cn Package (Domestic)
- trae-sg Package (Singapore CDN)
- trae-us Package (US CDN)
- linuxqq-nt
- CONTRIBUTORS.md
- No ${CARCH} in source_<arch> Rule
- zen-browser-twilight-bin
- Electron SUID Sandbox Practice
- Launcher Script Path Coupling Risk
- Local Source Hash Sync Rule
- pkgrel Revision Rule
- pkgver Versioning Rule
- Rolling Release Source Checksum Rule
- Source Alias Cache-Busting Rule
- Virtual Package (provides) Practice
- __init__.py
- __init__.py
- __init__.py
- __init__.py
- __init__.py
- __init__.py
- __init__.py
- __init__.py
- __init__.py
- blake2b hash builder registration (_HASH_BUILDERS)
- uv Package Manager
- get_effective_hash_algorithm method
- hash_algorithm config field (Settings + PackageConfig override)
- PackageUpdater hardcoded SHA512 elimination
- PKGBUILDEditor hash_algorithm parameterization
- B2 unit tests (hash + pkgbuild_editor)
- aria2c Multi-threaded Downloader
- makepkg Build Tool
- namcap PKGBUILD Linter
- ty Static Type Checker
- uv Package Manager

## God Nodes (most connected - your core abstractions)
1. `PKGBUILDEditor` - 73 edges
2. `ArchEnum` - 43 edges
3. `QQParser` - 42 edges
4. `PackageUpdater` - 35 edges
5. `BaseParser` - 26 edges
6. `PackageConfig` - 23 edges
7. `TraeParser` - 22 edges
8. `AUR 打包实践指南` - 20 edges
9. `NavicatPremiumCSParser` - 19 edges
10. `TestUpdateSourceArchEdgeCases` - 18 edges

## Surprising Connections (you probably didn't know these)
- `Push to AUR Workflow` --implements--> `Conventional Commits Standard`  [INFERRED]
  .github/workflows/push-to-aur.yml → CLAUDE.md
- `Push to AUR Workflow` --implements--> `.SRCINFO Sync Requirement`  [INFERRED]
  .github/workflows/push-to-aur.yml → docs/packaging-guide.md
- `Update Packages Workflow` --implements--> `Conventional Commits Standard`  [INFERRED]
  .github/workflows/update-packages.yml → CLAUDE.md
- `Update Packages Workflow` --implements--> `.SRCINFO Sync Requirement`  [INFERRED]
  .github/workflows/update-packages.yml → docs/packaging-guide.md
- `trae package config (TraeParser)` --references--> `Trae AI IDE by ByteDance (CDN variants)`  [INFERRED]
  scripts/config.yaml → packages/trae/README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Trae variant packages share makepkg cache + GCC lib issues** — pkg_trae, pkg_trae_sg, pkg_trae_us, pkg_trae_cn, issue_trae_makepkg_cache, issue_trae_gcc_libs [INFERRED 0.85]
- **Update → SRCINFO → Commit → AUR Push Pipeline** — github_workflows_update_packages, wf_arch_pkg_action, wf_aur_deploy_action, rules_srcinfo [INFERRED 0.85]
- **makepkg checksum / cache-busting rule cluster** — rules_source_alias_cache, rules_carch_in_source, rules_local_source_hash, rules_rolling_release_checksum, tool_makepkg [INFERRED 0.85]
- **B2 hash support implementation flow (Enum → Config → Updater)** — specs_hash_algorithm_enum, specs_blake2b_builder, specs_hash_algorithm_field, specs_pkgbuild_editor_api, specs_package_updater_hardcode_removal [EXTRACTED 0.95]
- **Trae CDN variant package family (CN/SG/US share API + version)** — scripts_config_yaml_trae_pkg, scripts_config_yaml_trae_sg_pkg, scripts_config_yaml_trae_us_pkg, scripts_config_yaml_trae_cn_pkg, packages_trae_bytedance_ide [INFERRED 0.85]
- **Package update pipeline (config → PackageUpdater → PKGBUILD)** — scripts_config_yaml, scripts_package_updater_module, specs_pkgbuild_editor_api, scripts_config_yaml_settings_hash_algorithm [INFERRED 0.85]

## Communities (105 total, 50 thin omitted)

### Community 0 - "ArchEnum"
Cohesion: 0.06
Nodes (20): Any, QQParser, QQ Linux 版本解析器（第三方聚合 API 数据源）, 解析 JSON 响应并返回 ``data`` 段；结构不符返回 None, 从 QQ 聚合 API 响应中提取版本号（``data.version``）, 从 QQ 聚合 API 响应中提取指定架构的下载 URL（原始未签名链接）, 从 QQ 聚合 API 响应中提取各架构的 b2 校验和, 请求未在 API urls 中的架构时返回 None (+12 more)

### Community 1 - "PackageUpdater"
Cohesion: 0.09
Nodes (16): ABC, 包更新器 整合fetch、parse和update三个流程  架构设计： 1. 并行更新所有维护的 AUR 包（使用 asyncio.gather） 2. 并行, BaseParser, Any, 解析器抽象基类，定义版本号、URL 和哈希解析接口。      子类需要实现的契约：      - ``parse_version``：从 API/页面响应中提, 从响应数据中提取原始下载 URL（写入 PKGBUILD 的 ``source_<arch>=()``）。          返回值必须是未经签名/鉴权处理的原, 获取可直接用于下载的 URL（程序内部使用，不写入 PKGBUILD）。          默认实现：直接返回 ``parse_url`` 的结果。子类可重写以, 从响应数据中提取各架构的校验和（可选）。          返回 ``{arch_value: checksum}`` 字典。返回 ``None`` 表示 pa (+8 more)

### Community 3 - "Path"
Cohesion: 0.08
Nodes (23): BaseModel, ArchEnum, HashAlgorithmEnum, ParserEnum, Enum, ConfigLoader, DownloadSettings, PackageConfig (+15 more)

### Community 4 - "BaseParser"
Cohesion: 0.06
Nodes (25): PackageUpdater, Path, 检查 PKGBUILD 文件是否存在          Args:             package_name: 包名             packa, 获取所有架构的原始下载 URL（用于写入 PKGBUILD 的 source 字段）。          走 parse_url 通道：QQ 等需要签名的包返回, 获取所有架构的可下载 URL（用于实际下载）。          走 resolve_url 通道：QQ 等需要签名的包在此步骤对 URL 签名，, 获取各架构校验和：优先用 parser 直接提供的 hashes，否则下载计算。          parser 通过 ``parse_hashes`` 返回, 下载文件并计算校验和          使用 Downloader 的并发下载功能，并行下载单个包的所有架构, 包更新器，整合fetch、parse和update流程 (+17 more)

### Community 5 - "ZenParser"
Cohesion: 0.09
Nodes (19): Path, 更新 source URL 时保留 :: 别名, update_source（arch 特定）替换逻辑的边界条件测试, URL 含 ${_gh}（花括号）时保留 shell 变量，不更新, URL 含 $_gh（无花括号）时同样应保留，等价于 ${_gh}, 别名含 ${pkgver}、URL 硬编码时，保留别名、替换 URL, 单行多条目：替换远程 URL，保留本地源文件, 缺失 source_<arch> 字段时不破坏其它内容 (+11 more)

### Community 7 - "QQParser"
Cohesion: 0.09
Nodes (14): Any, Zen Browser 每夜版解析器      从 GitHub Releases API 获取 twilight-1 标签的发布信息。     twiligh, 从 GitHub Release 的 name 字段提取版本号          release name 格式: "Twilight build - 1.20, 从 GitHub Release assets 中提取指定架构的下载 URL, ZenParser, _make_zen_response(), Any, 构造 Zen GitHub Release JSON 响应 (+6 more)

### Community 8 - "AUR 打包实践指南"
Cohesion: 0.14
Nodes (13): AUR 打包实践指南, license [官方规范], pkgdesc [官方规范], provides 和 conflicts [推荐实践], Shell 补全 [推荐实践], source 声明 [推荐实践], .SRCINFO [官方规范], 代码质量 [推荐实践] (+5 more)

### Community 9 - "TraeParser"
Cohesion: 0.14
Nodes (9): TestExtractExtensionFromUrl, TestExtractFilenameFromUrl, TestGenerateDownloadFilename, extract_extension_from_url(), extract_filename_from_url(), generate_download_filename(), 从 URL 中提取文件扩展名（包含点号）      支持复合扩展名（如 .tar.gz）和普通扩展名, 生成标准化的下载文件名      格式: {package_name}_{version}_{arch}{extension}     自动从 URL 提取扩展 (+1 more)

### Community 10 - "extract_extension_from_url"
Cohesion: 0.16
Nodes (8): Any, Enum, Trae IDE 版本解析器，从 JSON API 提取版本号和下载链接, 解析响应，返回 data.data.manifest.linux 字典；非法输入或结构缺失返回 None, TraeParser, TraeRegion, TestTraeParseUrl, TestTraeParseVersion

### Community 11 - "compare_versions"
Cohesion: 0.14
Nodes (6): TestCompareVersions, TestParseVersion, compare_versions(), parse_version(), 比较两个版本号      Args:         version1: 第一个版本号         version2: 第二个版本号      Return, 解析版本号为可比较的组成部分      Args:         version: 版本字符串，如 "3.2.22_251203", "17.3.5"

### Community 12 - "NavicatPremiumCSParser"
Cohesion: 0.20
Nodes (5): NavicatPremiumCSParser, Any, Navicat Premium CS 版本解析器, TestNavicatParseUrl, TestNavicatParseVersion

### Community 13 - "AUR 包自动更新工具"
Cohesion: 0.13
Nodes (13): Commit 规范, 分支策略, 提交流程, 添加新软件包, 贡献指南, AUR 包自动更新工具, 开发, 快速开始 (+5 more)

### Community 14 - "._update_scalar_field"
Cohesion: 0.14
Nodes (4): 更新校验和字段。          arch=None 更新非架构特定 sums=()（arch=('any') 包），否则更新 sums_<arch>=()。, 替换 ^field=.*$ 整行为 field=value（MULTILINE）。字段不存在时无操作。          用 lambda 返回替换文本，避免, 返回 ^field=(.*)$ 的捕获值；字段不存在返回 None。, 取标量并按 int 解析；缺失或解析失败返回 default。

### Community 15 - "设计"
Cohesion: 0.15
Nodes (12): 1. HashAlgorithmEnum 新增 B2, 2. 注册 blake2b 构建器, 3. 配置模型新增 hash_algorithm 字段, 4. config.yaml 配置, 5. PKGBUILDEditor API 清理, 6. PackageUpdater 消除硬编码, 7. 单元测试补充, B2 (BLAKE2b) 哈希算法支持设计 (+4 more)

### Community 16 - "TestPKGBUILDEditorEpoch"
Cohesion: 0.20
Nodes (5): pkgbuild(), update_epoch 和 get_epoch 测试, 无 epoch 行时在 pkgver 前插入, new_epoch=None 时不做任何修改, TestPKGBUILDEditorEpoch

### Community 17 - "._update_source_field"
Cohesion: 0.25
Nodes (3): 文本是否包含 shell 变量引用（${VAR} 或 $VAR/$_VAR）, source 条目是否为远程 URL（带 :: 别名或以协议头开头）, 更新 source / source_<arch> 字段的远程 URL。          - 支持单行/多行、单条目/多条目数组；本地源条目（如 launch

### Community 18 - "test_pkgbuild_editor.py"
Cohesion: 0.29
Nodes (5): Commit 规范, graphify, 开发命令, 注意事项, 添加新软件包

### Community 19 - "类型注解规范"
Cohesion: 0.33
Nodes (6): AppImage 依赖分析 [推荐实践], AppImage 解包, AppRun 启动问题 [推荐实践], 捆绑库冲突与 LD_PRELOAD [推荐实践], 清理冗余文件 [推荐实践], 解包流程 [推荐实践]

### Community 20 - "post-commit"
Cohesion: 0.33
Nodes (6): Electron 直装（tarball）, source 文件排除 [项目约定], SUID sandbox [项目约定], 启动脚本 [项目约定], 完整示例, 构建选项 [项目约定]

### Community 21 - "post-checkout"
Cohesion: 0.40
Nodes (4): 基本规则, 类型存根, 类型检查, 类型注解规范

### Community 23 - "navicat17-premium-zh-cn"
Cohesion: 0.40
Nodes (5): deb 解包, 内部结构 [推荐实践], 捆绑库处理 [推荐实践], 清理冗余文件 [推荐实践], 解包与清理 [推荐实践]

### Community 24 - "trae-sg"
Cohesion: 0.40
Nodes (5): DLAGENTS 自定义下载代理 [推荐实践], 参考, 常见陷阱, 格式与变量, 示例：URL 签名（linuxqq-nt）

### Community 27 - "trae-us"
Cohesion: 0.40
Nodes (5): strip 与 debug 包 [推荐实践], VCS 包 [推荐实践], 构建标志 [推荐实践], 构建流程 [官方规范], 源码编译

### Community 28 - "zen-browser-twilight.sh"
Cohesion: 0.40
Nodes (4): post-commit script, GRAPHIFY_CHANGED, GRAPHIFY_REBUILD_LOG, PYTHONHASHSEED

### Community 30 - "navicat.sh"
Cohesion: 0.40
Nodes (4): structure/, 命名, 添加新包快照, 用途

### Community 31 - "trae-cn.sh"
Cohesion: 0.50
Nodes (4): epoch, pkgrel, pkgver, 版本 [官方规范]

### Community 32 - "trae.sh"
Cohesion: 0.50
Nodes (4): 依赖 [官方规范], 虚拟包 [推荐实践], 运行时加载依赖 [推荐实践], 预编译二进制包的依赖分析 [推荐实践]

### Community 33 - "trae.sh"
Cohesion: 0.50
Nodes (3): post-checkout script, GRAPHIFY_REBUILD_LOG, PYTHONHASHSEED

### Community 34 - "trae.sh"
Cohesion: 0.50
Nodes (3): QQ_DEFAULT_FLAGS, QQ_USER_FLAGS, linuxqq.sh script

### Community 35 - "commit-msg"
Cohesion: 0.50
Nodes (3): Feedback, Install, navicat17-premium-zh-cn

### Community 36 - "CONTRIBUTING Guide"
Cohesion: 0.50
Nodes (3): Feedback, Install, trae-sg

### Community 37 - "README - AUR Package Auto-Updater"
Cohesion: 0.50
Nodes (3): Feedback, Install, trae-us

### Community 39 - "PKGBUILDEditor"
Cohesion: 0.10
Nodes (8): BaseException, PKGBUILD 中不存在该算法的校验和时返回空字符串, TestPKGBUILDEditorContextManager, TestPKGBUILDEditorGetters, TestPKGBUILDEditorUpdate, PKGBUILDEditor, Path, PKGBUILD 文件编辑器，支持上下文管理器自动保存

### Community 40 - "Dev-Main Branch Strategy"
Cohesion: 0.50
Nodes (3): MOZ_APP_LAUNCHER, zen-browser-twilight.sh script, ZEN_USER_FLAGS

### Community 41 - "calculate_file_hash"
Cohesion: 0.19
Nodes (9): Protocol, Path, calculate_file_hash 测试, 文件不存在抛出 FileNotFoundError, TestCalculateFileHash, calculate_file_hash(), _Hash, Path (+1 more)

### Community 46 - "config.yaml (global + per-package settings)"
Cohesion: 0.16
Nodes (15): linuxqq-nt package (Electron QQ), navicat17-premium-zh-cn package (Chinese Simplified), Trae AI IDE by ByteDance (CDN variants), zen-browser-twilight-bin package (Firefox-based nightly), config.yaml (global + per-package settings), bt-dualboot-ng package config (PyPIParser), navicat package config (NavicatPremiumCSParser), qq package config (QQParser) (+7 more)

### Community 47 - "AUR 包已知问题"
Cohesion: 0.20
Nodes (9): AUR 包已知问题, makepkg 缓存冲突, Navicat（navicat17-premium-zh-cn）, tarball 内包含冗余文件, Trae 系列（trae / trae-sg / trae-us / trae-cn）, 修改本地源文件后 hash 不匹配, 捆绑 GCC 运行时库导致 ckg 索引崩溃, 捆绑 libsystemd 与系统 libmount 不兼容 (+1 more)

### Community 48 - "PackageUpdater (Fetch → Parse → Update coordinator)"
Cohesion: 0.40
Nodes (3): scripts/, 前置依赖, 模块结构

### Community 49 - "Update Packages Workflow"
Cohesion: 0.48
Nodes (7): Conventional Commits Standard, Push to AUR Workflow, Update Packages Workflow, .SRCINFO Sync Requirement, awsl1414/archlinux-package-action, github-actions-deploy-aur Action, Chinese DNS Resolution for cdn-go.cn

### Community 53 - "trae"
Cohesion: 0.50
Nodes (3): Feedback, Install, trae

### Community 59 - "linuxqq-nt"
Cohesion: 0.50
Nodes (3): Feedback, Install, linuxqq-nt

### Community 62 - "zen-browser-twilight-bin"
Cohesion: 0.50
Nodes (3): Feedback, Install, zen-browser-twilight-bin

## Knowledge Gaps
- **139 isolated node(s):** `linuxqq.sh script`, `QQ_DEFAULT_FLAGS`, `QQ_USER_FLAGS`, `navicat.sh script`, `LD_PRELOAD` (+134 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **50 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PackageUpdater` connect `BaseParser` to `ArchEnum`, `PackageUpdater`, `Path`, `QQParser`, `PKGBUILDEditor`, `extract_extension_from_url`, `NavicatPremiumCSParser`?**
  _High betweenness centrality (0.156) - this node is a cross-community bridge._
- **Why does `PKGBUILDEditor` connect `PKGBUILDEditor` to `PackageUpdater`, `Path`, `BaseParser`, `ZenParser`, `._update_scalar_field`, `TestPKGBUILDEditorEpoch`, `._update_source_field`?**
  _High betweenness centrality (0.144) - this node is a cross-community bridge._
- **Why does `ArchEnum` connect `Path` to `ArchEnum`, `PackageUpdater`, `BaseParser`, `QQParser`, `extract_extension_from_url`, `NavicatPremiumCSParser`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Are the 47 inferred relationships involving `PKGBUILDEditor` (e.g. with `PackageUpdater` and `TestPKGBUILDEditorContextManager`) actually correct?**
  _`PKGBUILDEditor` has 47 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `ArchEnum` (e.g. with `PackageUpdater` and `ConfigLoader`) actually correct?**
  _`ArchEnum` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 36 inferred relationships involving `QQParser` (e.g. with `PackageUpdater` and `.__init__()`) actually correct?**
  _`QQParser` has 36 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `PackageUpdater` (e.g. with `ArchEnum` and `HashAlgorithmEnum`) actually correct?**
  _`PackageUpdater` has 16 INFERRED edges - model-reasoned connections that need verification._