# Graph Report - aur-packages  (2026-09-05)

## Corpus Check
- 63 files · ~16,041 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 579 nodes · 820 edges · 104 communities (40 shown, 51 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 45 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d96cf0ea`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- .load_from_yaml
- .__exit__
- AppImage Dependency Analysis Practice
- package_updater.py
- PackageUpdater
- Path
- Rationale: zen-browser-twilight-bin uses b2sums but updater hardcoded SHA512
- AUR 打包实践指南
- extract_extension_from_url
- compare_versions
- AUR 包自动更新工具
- ._update_scalar_field
- 设计
- TestPKGBUILDEditorEpoch
- ._update_source_field
- AGENTS.md
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
- _Hash
- navicat.sh
- trae-cn.sh
- CLAUDE.md Project Instructions
- linuxqq-nt package (Electron QQ)
- AUR 包已知问题
- scripts/
- Update Packages Workflow
- trae-sg/trae.sh
- trae/trae.sh
- trae-us/trae.sh
- trae
- 校验和 [官方规范]
- commit-msg
- CONTRIBUTING Guide
- README - AUR Package Auto-Updater
- Dev-Main Branch Strategy
- linuxqq-nt
- CONTRIBUTORS.md
- BaseParser Plugin Pattern
- zen-browser-twilight-bin
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
- PackageUpdater (Fetch → Parse → Update coordinator)
- blake2b hash builder registration (_HASH_BUILDERS)
- get_effective_hash_algorithm method
- hash_algorithm config field (Settings + PackageConfig override)
- PackageUpdater hardcoded SHA512 elimination
- PKGBUILDEditor hash_algorithm parameterization
- B2 unit tests (hash + pkgbuild_editor)
- aria2c Multi-threaded Downloader
- makepkg Build Tool
- namcap PKGBUILD Linter
- uv Package Manager
- ApiParser
- Downloader
- Fetcher
- navicat17-premium-zh-cn package (Chinese Simplified)
- Trae AI IDE by ByteDance (CDN variants)
- zen-browser-twilight-bin package (Firefox-based nightly)
- HashAlgorithmEnum (SHA256/SHA512/B2)

## God Nodes (most connected - your core abstractions)
1. `PKGBUILDEditor` - 75 edges
2. `PackageUpdater` - 30 edges
3. `ApiParser` - 27 edges
4. `PackageConfig` - 22 edges
5. `AUR 打包实践指南` - 20 edges
6. `Fetcher` - 18 edges
7. `TestUpdateSourceArchEdgeCases` - 17 edges
8. `HashAlgorithmEnum` - 15 edges
9. `ArchEnum` - 14 edges
10. `calculate_file_hash()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `Push to AUR Workflow` --implements--> `Conventional Commits Standard`  [INFERRED]
  .github/workflows/push-to-aur.yml → CLAUDE.md
- `Push to AUR Workflow` --implements--> `.SRCINFO Sync Requirement`  [INFERRED]
  .github/workflows/push-to-aur.yml → docs/packaging-guide.md
- `Update Packages Workflow` --implements--> `Conventional Commits Standard`  [INFERRED]
  .github/workflows/update-packages.yml → CLAUDE.md
- `Update Packages Workflow` --implements--> `.SRCINFO Sync Requirement`  [INFERRED]
  .github/workflows/update-packages.yml → docs/packaging-guide.md
- `PackageUpdater` --uses--> `ArchEnum`  [INFERRED]
  scripts/core/package_updater.py → scripts/constants/constants.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Update → SRCINFO → Commit → AUR Push Pipeline** — github_workflows_update_packages, wf_arch_pkg_action, wf_aur_deploy_action, rules_srcinfo [INFERRED 0.85]
- **makepkg checksum / cache-busting rule cluster** — rules_source_alias_cache, rules_carch_in_source, rules_local_source_hash, rules_rolling_release_checksum, tool_makepkg [INFERRED 0.85]
- **B2 hash support implementation flow (Enum → Config → Updater)** — specs_hash_algorithm_enum, specs_blake2b_builder, specs_hash_algorithm_field, specs_pkgbuild_editor_api, specs_package_updater_hardcode_removal [EXTRACTED 0.95]

## Communities (104 total, 51 thin omitted)

### Community 0 - ".load_from_yaml"
Cohesion: 0.15
Nodes (9): Path, linuxqq-nt 包未设置 hash_algorithm，使用全局默认, 空 YAML 文件抛出 ValueError, 不存在的文件抛出 FileNotFoundError, navicat URL 静态写死在 PKGBUILD，update_source_url 为 False, 全局默认 hash_algorithm 为 b2, 全局默认不忽略 SSL 错误（证书校验开启）, zen-browser 使用全局默认 b2（无需包级覆盖） (+1 more)

### Community 3 - "package_updater.py"
Cohesion: 0.08
Nodes (27): BaseModel, Enum, fixture, ArchEnum, HashAlgorithmEnum, 包更新器 整合fetch、parse和update三个流程 架构设计： 1. 并行更新所有维护的 AUR 包（使用 asyncio.gather） 2.…, ApiSettings, ConfigLoader (+19 more)

### Community 4 - "PackageUpdater"
Cohesion: 0.09
Nodes (19): PackageUpdater, Path, 检查 PKGBUILD 文件是否存在 Args: package_config: 包配置 Returns: True 如果文件存在，False 否则, 从 ``parsed.hashes`` 中挑选出支持架构的校验和。 返回 ``{arch_value:…, 获取各架构校验和：优先用 helper API 提供的 hashes，否则下载计算。 helper 通过 ``data.hashes``…, 下载文件并计算校验和（回退路径） 使用 Downloader 的并发下载功能，并行下载单个包的所有架构, 包更新器，整合fetch、parse和update流程, 处理版本不更新的情况（当前版本 >= 新版本） 复用 update_package 已创建的 editor，避免重复加载 PKGBUILD。 两种场景： 1.… (+11 more)

### Community 5 - "Path"
Cohesion: 0.09
Nodes (19): Path, 更新 source URL 时保留 :: 别名, update_source（arch 特定）替换逻辑的边界条件测试, URL 含 ${_gh}（花括号）时保留 shell 变量，不更新, URL 含 $_gh（无花括号）时同样应保留，等价于 ${_gh}, 别名含 ${pkgver}、URL 硬编码时，保留别名、替换 URL, 单行多条目：替换远程 URL，保留本地源文件, 缺失 source_<arch> 字段时不破坏其它内容 (+11 more)

### Community 8 - "AUR 打包实践指南"
Cohesion: 0.14
Nodes (13): AUR 打包实践指南, license [官方规范], pkgdesc [官方规范], provides 和 conflicts [推荐实践], Shell 补全 [推荐实践], source 声明 [推荐实践], .SRCINFO [官方规范], 代码质量 [推荐实践] (+5 more)

### Community 9 - "extract_extension_from_url"
Cohesion: 0.15
Nodes (9): TestExtractExtensionFromUrl, TestExtractFilenameFromUrl, TestGenerateDownloadFilename, extract_extension_from_url(), extract_filename_from_url(), generate_download_filename(), 从 URL 中提取文件扩展名（包含点号） 支持复合扩展名（如 .tar.gz）和普通扩展名, 生成标准化的下载文件名 格式: {package_name}_{version}_{arch}{extension} 自动从 URL… (+1 more)

### Community 11 - "compare_versions"
Cohesion: 0.18
Nodes (6): TestCompareVersions, TestParseVersion, compare_versions(), parse_version(), 比较两个版本号 Args: version1: 第一个版本号 version2: 第二个版本号 Returns: -1: version1 <…, 解析版本号为可比较的组成部分 Args: version: 版本字符串，如 "3.2.22_251203", "17.3.5" Returns:…

### Community 13 - "AUR 包自动更新工具"
Cohesion: 0.13
Nodes (13): Commit 规范, 分支策略, 提交流程, 添加新软件包, 贡献指南, AUR 包自动更新工具, 开发, 快速开始 (+5 more)

### Community 14 - "._update_scalar_field"
Cohesion: 0.14
Nodes (4): 更新校验和字段。 arch=None 更新非架构特定 sums=()（arch=('any') 包），否则更新 sums_<arch>=()。, 替换 ^field=.*$ 整行为 field=value（MULTILINE）。字段不存在时无操作。 用 lambda 返回替换文本，避免 value…, 返回 ^field=(.*)$ 的捕获值；字段不存在返回 None。, 取标量并按 int 解析；缺失或解析失败返回 default。

### Community 15 - "设计"
Cohesion: 0.15
Nodes (12): 1. HashAlgorithmEnum 新增 B2, 2. 注册 blake2b 构建器, 3. 配置模型新增 hash_algorithm 字段, 4. config.yaml 配置, 5. PKGBUILDEditor API 清理, 6. PackageUpdater 消除硬编码, 7. 单元测试补充, B2 (BLAKE2b) 哈希算法支持设计 (+4 more)

### Community 16 - "TestPKGBUILDEditorEpoch"
Cohesion: 0.25
Nodes (4): update_epoch 和 get_epoch 测试, 无 epoch 行时在 pkgver 前插入, new_epoch=None 时不做任何修改, TestPKGBUILDEditorEpoch

### Community 17 - "._update_source_field"
Cohesion: 0.25
Nodes (4): 文本是否包含 shell 变量引用（${VAR} 或 $VAR/$_VAR）, source 条目是否为远程 URL（带 :: 别名或以协议头开头）, 更新 source / source_<arch> 字段的远程 URL。 - 支持单行/多行、单条目/多条目数组；本地源条目（如…, 更新 source URL，保留别名与本地源条目；URL 含 shell 变量时跳过。 arch=None 更新非架构特定…

### Community 18 - "AGENTS.md"
Cohesion: 0.29
Nodes (5): Commit 规范, graphify, 开发命令, 注意事项, 添加新软件包

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
Nodes (8): PKGBUILD 中不存在该算法的校验和时返回空字符串, TestPKGBUILDEditorContextManager, TestPKGBUILDEditorGetters, TestPKGBUILDEditorUpdate, PKGBUILDEditor, Path, PKGBUILD 文件编辑器，支持上下文管理器自动保存, 获取当前校验和值。 arch=None 读取非架构特定 sums=()（arch=('any') 包），否则读取 sums_<arch>=()。

### Community 40 - "zen-browser-twilight.sh"
Cohesion: 0.50
Nodes (3): MOZ_APP_LAUNCHER, zen-browser-twilight.sh script, ZEN_USER_FLAGS

### Community 47 - "AUR 包已知问题"
Cohesion: 0.20
Nodes (9): AUR 包已知问题, makepkg 缓存冲突, Navicat（navicat17-premium-zh-cn）, tarball 内包含冗余文件, Trae 系列（trae / trae-sg / trae-us / trae-cn）, 修改本地源文件后 hash 不匹配, 捆绑 GCC 运行时库导致 ckg 索引崩溃, 捆绑 libsystemd 与系统 libmount 不兼容 (+1 more)

### Community 48 - "scripts/"
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

### Community 105 - "ApiParser"
Cohesion: 0.08
Nodes (19): ApiParser, Any, helper API 统一响应解析器（唯一解析器） 数据源：``aur-packages-helper`` 项目的 ``GET…, helper API 统一响应解析器。 一次 ``parse`` 返回完整的 ``ParsedPackage``，避免版本/URL/hash 分别解析时…, 解析 helper API 响应为 ``ParsedPackage``；结构不符返回 None。, 解析 JSON 响应并返回 ``data`` 段；结构不符返回 None。, ApiParser 单元测试 数据源：``aur-packages-helper`` 的 ``GET /api/v1/packages/{name}``…, data 中无 hashes 字段时 hashes 为空字典（调用方回退下载），不算解析失败 (+11 more)

### Community 106 - "Downloader"
Cohesion: 0.13
Nodes (12): _make_downloader(), Any, Downloader 单元测试（aria2c 参数拼装）, 构造 Downloader，mock 掉 aria2c 存在性检查（CI 环境可能未安装）, 默认开启证书校验（--check-certificate=true）, check_certificate=False 时传给 aria2c --check-certificate=false, TestBuildBaseArgs, Downloader (+4 more)

### Community 107 - "Fetcher"
Cohesion: 0.12
Nodes (25): asyncio, Fetcher, HTTP 客户端模块 处理 ``aur-packages-helper`` API 的响应语义： - 成功：HTTP 200，body…, 从 helper 错误响应 body 中提取 ``message`` 字段。 非 JSON、非对象或缺字段时返回 None，由调用方回退到 HTTP…, HTTP 客户端封装，按 helper API 状态码语义处理请求与重试, 获取文本数据。 - HTTP 200 → 返回 body 文本 - 4xx 永久错误 → 记日志，返回 None（不重试） - 429/5xx 或网络异常 →…, 错误 body 的 message 被提取（通过日志间接验证：永久错误路径不抛异常）, 默认开启 SSL 证书校验（verify=True 传入 httpx 客户端） (+17 more)

## Knowledge Gaps
- **137 isolated node(s):** `linuxqq.sh script`, `QQ_DEFAULT_FLAGS`, `QQ_USER_FLAGS`, `navicat.sh script`, `LD_PRELOAD` (+132 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 299 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **51 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PKGBUILDEditor` connect `PKGBUILDEditor` to `.__exit__`, `package_updater.py`, `PackageUpdater`, `Path`, `._update_scalar_field`, `TestPKGBUILDEditorEpoch`, `._update_source_field`?**
  _High betweenness centrality (0.167) - this node is a cross-community bridge._
- **Why does `PackageUpdater` connect `PackageUpdater` to `package_updater.py`, `PKGBUILDEditor`, `ApiParser`, `Downloader`, `Fetcher`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Why does `ApiParser` connect `ApiParser` to `Downloader`, `package_updater.py`, `PackageUpdater`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `PKGBUILDEditor` (e.g. with `PackageUpdater` and `TestPKGBUILDEditorContextManager`) actually correct?**
  _`PKGBUILDEditor` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `PackageUpdater` (e.g. with `ArchEnum` and `HashAlgorithmEnum`) actually correct?**
  _`PackageUpdater` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `ApiParser` (e.g. with `PackageUpdater` and `TestApiParseHashes`) actually correct?**
  _`ApiParser` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `PackageConfig` (e.g. with `PackageUpdater` and `ArchEnum`) actually correct?**
  _`PackageConfig` has 4 INFERRED edges - model-reasoned connections that need verification._