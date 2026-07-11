# AUR 打包实践指南

本文档面向本项目中的 AUR 包维护，分为三个层级：

- **[官方规范]**：Arch Wiki / AUR 要求，必须遵守
- **[推荐实践]**：经过验证的最佳做法，建议遵守
- **[项目约定]**：本项目内部约定，保持一致性

通用 Arch 打包规范请参考 [Arch Wiki - Creating packages](https://wiki.archlinux.org/title/Creating_packages)。

---

## 版本 [官方规范]

### pkgver

- 应与上游发布的版本号一致
- 可包含字母、数字、点和下划线，**不允许连字符**（`-`），需替换为下划线（`_`）
- 上游使用时间戳版本时，使用 ISO 8601 倒序格式（如 `20141030` 而非 `30102014`）
- 可通过 `vercmp` 工具验证版本排序

### pkgrel

- 修改 `source`、`depends`、`package()` 等影响打包输出的字段时，必须递增 `pkgrel`
- 修改 `pkgver` 时，`pkgrel` 重置为 `1`

### epoch

- 用于强制将包视为比任何具有较低 epoch 的版本更新，值为非负整数，默认为 `0`
- 仅在版本号方案变更导致正常版本比较失效时使用
- 除非绝对必要，不应使用

## .SRCINFO [官方规范]

AUR 提交必须包含 `.SRCINFO`，且与 PKGBUILD 保持同步：

```bash
makepkg --printsrcinfo > .SRCINFO
```

## license [官方规范]

- Arch Linux 使用 SPDX 许可证标识符（如 `MIT`、`Apache-2.0`、`GPL-3.0-or-later`）
- BSD、MIT 等许可族使用 SPDX 标识符（如 `BSD-3-Clause`），但需提供对应的许可证文件
- 非标准许可证使用 `LicenseRef-license-name` 格式（`custom:` 不是有效 SPDX 标识符，namcap 会报错）
- 组合许可证遵循 SPDX 语法（如 `'Apache-2.0 WITH LLVM-exception'`），必须为单引号包裹的单个字符串

安装到 `/usr/share/licenses/${pkgname}/`：

```bash
install -Dm644 "LICENSE.txt" "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
```

## pkgdesc [官方规范]

- 不应包含包名（`namcap` 会警告 `Description should not contain the package name`）
- 应简洁描述包的功能，可包含上游名称或功能区分信息

```bash
# ✓ 正确
pkgdesc="AI-powered IDE by ByteDance"
pkgdesc="Navicat Premium is a multi-connection database development tool. (Chinese Simplified)"

# ✗ 错误（包含包名 trae）
pkgdesc="Trae - AI-powered IDE by ByteDance"
```

## 依赖 [官方规范]

| 字段 | 用途 |
|------|------|
| `depends` | 运行时依赖 |
| `makedepends` | 构建时依赖 |
| `checkdepends` | 测试时依赖 |
| `optdepends` | 可选功能依赖，应附简短说明，让用户明确安装后获得什么 |

关键规则：

- `depends` 应列出所有直接依赖，即使某些已被其他依赖传递引入
- `makedepends` 中 `base-devel` 视为已安装，不要包含其子包
- `depends` 不应重复出现在 `makedepends` 中（`depends` 隐含在构建时也需要）
- 可指定版本约束：`depends=('foobar>=1.8.0')`，需要多个约束时重复声明
- `optdepends` 应列出提供**实际可用功能**的具体包，而非仅提供框架/运行时的包：

```bash
# ✓ 列出具体词典包（安装后即可用）
optdepends=('hunspell-en_US: English spell checking')

# ✗ 仅列出框架包（安装后无词典数据，用户看不到功能）
optdepends=('hunspell: Spell checking')
```
- 若依赖名为库文件（如 `libfoobar.so`），makepkg 会自动检测并附加 soname 版本

依赖确认方式：

- 通过 `ldd`、`namcap`（或 `find-libdeps`）检查二进制实际依赖
- 只声明**实际依赖**的系统库，不基于框架理论推断

### 预编译二进制包的依赖分析 [推荐实践]

预编译二进制包（Electron tarball、deb、AppImage）常捆绑大量运行时库。依赖分析步骤：

1. 使用 `namcap *.pkg.tar.zst` 和 `find-libdeps` 检查实际依赖
2. 区分 **E（Error）** 和 **W（Warning）** 输出：Error 级别的缺失依赖必须添加
3. `namcap` 报告的 `implicitly satisfied` 依赖已被现有 `depends` 的传递依赖覆盖，无需重复添加

AppImage 包几乎捆绑所有依赖，`depends` 只需列出**未捆绑的系统库**（如 `fontconfig`、`freetype2`）：

```bash
# AppImage 捆绑了 Qt6、X11、curl、SSL 等，只有 fontconfig/freetype2 未捆绑
depends=('fontconfig' 'freetype2' 'hicolor-icon-theme')
```

Electron 包依赖声明应覆盖主二进制链接的系统库：

```bash
# Electron 主二进制链接的系统库
depends=('nss' 'alsa-lib' 'gtk3' 'at-spi2-core' 'libsecret' 'libxkbfile' 'zeromq')
```

### 运行时加载依赖 [推荐实践]

部分应用（Firefox 系浏览器、基于 GStreamer/FFmpeg 插件框架的应用）通过 `dlopen` 在运行时加载媒体编解码器，**不出现在 `ldd` 输出中**。这些依赖需通过以下方式识别：

1. 测试实际功能（如视频播放、音频解码），观察缺失库的报错
2. 对比 AUR 官方同类包的 `depends` 列表，排查差异

修改依赖时，应与 AUR 官方同类包（如 `firefox`、`zen-browser-bin`）交叉验证。官方包通常经过社区长期维护，其依赖列表是可靠的参考基线。如需偏离官方包的依赖声明（如移除 `systemd-libs`、替换 `ffmpeg4.4` 为 `ffmpeg`），必须提供 `namcap`/`find-libdeps` 的审计证据。

### 虚拟包 [推荐实践]

优先使用虚拟包（provides 而非具体实现）以提高兼容性：

| 虚拟包 | 提供者 | 用途 |
|--------|--------|------|
| `pulse-native-provider` | `pipewire-pulse`、`pulseaudio` | 音频支持（PulseAudio/PipeWire 兼容） |

```bash
# ✓ 使用虚拟包（兼容 PulseAudio 和 PipeWire）
depends=('pulse-native-provider')

# ✗ 绑定具体实现
depends=('libpulse')
```

## 函数职责 [官方规范]

| 函数 | 职责 |
|------|------|
| `prepare()` | 补丁、预处理 |
| `build()` | 编译 |
| `check()` | 测试 |
| `package()` | 安装文件到 `${pkgdir}` |

预编译二进制包通常省略 `build()` 和 `check()`，只在 `prepare()` 中解包，`package()` 中安装。

`package()` 在 fakeroot 环境中运行，`chmod 4755` 等权限操作只影响 `${pkgdir}` 内的元数据，不会修改宿主机文件。

## 校验和 [官方规范]

- 优先使用 `sha256sums` 或 `b2sums`
- 不使用 `SKIP`，除非源文件动态变化无法固定（如 VCS 源）

### 滚动发布源 [推荐实践]

Nightly/twilight 等滚动发布版本使用固定 URL（如 `twilight-1` tag），每次上游更新覆盖同一文件。虽然文件名不变，但**每个特定版本的 tarball 内容是固定的**——仍必须固定校验和，不能用 `SKIP`。

这与 VCS 源（`git+https://...`，每次 pull 内容不同）是本质区别。滚动发布源的校验和由自动化工具在版本更新时同步更新。

```bash
# ✓ 固定校验和（每次版本更新时由工具同步）
b2sums_x86_64=('a1b2c3...')

# ✗ 使用 SKIP（移除完整性验证，二进制下载无法防篡改）
b2sums_x86_64=('SKIP')
```

## 代码质量 [推荐实践]

提交前使用 namcap 检查：

```bash
namcap PKGBUILD
namcap *.pkg.tar.zst
```

可检测缺失/多余依赖、不规范文件路径等问题。

## 变量约定 [项目约定]

当 `pkgname` 与上游二进制/目录名不同时（如 `pkgname=linuxqq-nt` 但上游使用 `linuxqq`），定义私有变量存放上游名称，避免全文硬编码：

```bash
_pkgname=linuxqq
pkgname=${_pkgname}-nt
```

对重复出现的路径和 URL，同样提取为变量：

```bash
_installdir="/opt/${pkgname}"           # 安装目标路径
_gh='https://github.com/org/repo/releases/download/v1'  # 下载基址
```

**判断标准**：同一字面字符串出现 3 次以上时，应提取为变量。这减少更新时的遗漏风险，也使 `package()` 函数更易读。

注意：`_pkgname` 等私有变量会出现在 `makepkg --printsrcinfo` 的输出中（作为 `source` 文件名的一部分），确保其命名不会与 makepkg 内部变量冲突。

## 文件操作 [推荐实践]

批量复制使用 `cp -a`（保留权限、时间戳、符号链接）：

```bash
cp -a "${srcdir}/app/." "${pkgdir}/opt/${pkgname}/"
```

安装单个文件使用 `install`（显式设定权限）：

```bash
install -Dm755 "${srcdir}/launcher.sh" "${pkgdir}/usr/bin/${pkgname}"
install -Dm644 "${srcdir}/app.desktop" "${pkgdir}/usr/share/applications/${pkgname}.desktop"
```

## source 声明 [推荐实践]

`source` 数组中的文件名必须唯一（`SRCDEST` 目录所有包共享）。若上游 URL 中的文件名可能冲突，使用 `::` 语法重命名：

```bash
source=("${pkgname}-${pkgver}.tar.gz::https://github.com/user/repo/archive/v${pkgver}.tar.gz")
```

- `.install` 文件由 makepkg 自动识别，不应加入 `source` 数组
- `.sig`、`.sign`、`.asc` 后缀的文件被自动识别为 PGP 签名
- 架构特定的源使用 `source_x86_64=()` 等后缀，需对应 `<algo>sums_x86_64=()` 等校验和数组（如 `b2sums_x86_64=()`、`sha512sums_x86_64=()`）
- URL 和文件名中的架构标识应使用 `${CARCH}` 替代硬编码值（`namcap` 会警告 `Reference to x86_64 should be changed to $CARCH`）：

**但是**，`source_<arch>` 数组中**不能使用 `${CARCH}`**。`makepkg --printsrcinfo` 在生成 `.SRCINFO` 时会就地展开 `${CARCH}`，如果 CI 运行在 x86_64 上，aarch64 的 source URL 也会被解析为 x86_64，导致 aarch64 用户下载到错误的文件。

```bash
# ✓ 硬编码架构（确保 .SRCINFO 正确）
source_x86_64=("${pkgname}-x86_64-${pkgver}.AppImage::https://example.com/app-x86_64.AppImage")
source_aarch64=("${pkgname}-aarch64-${pkgver}.AppImage::https://example.com/app-aarch64.AppImage")

# ✗ 使用 ${CARCH}（CI 生成 .SRCINFO 时 aarch64 URL 会被解析为 x86_64）
source_x86_64=("${pkgname}-${CARCH}-${pkgver}.AppImage::https://example.com/app-${CARCH}.AppImage")
source_aarch64=("${pkgname}-${CARCH}-${pkgver}.AppImage::https://example.com/app-${CARCH}.AppImage")
```

`${CARCH}` 在 `prepare()` / `package()` 等函数中使用是安全的——函数体不会被 `makepkg --printsrcinfo` 展开。

## DLAGENTS 自定义下载代理 [推荐实践]

`DLAGENTS` 用于自定义 makepkg 下载源码时调用的命令。常见用途：

- 替换默认的 curl/wget 为 aria2c 等支持多线程的下载器
- 走镜像站（替换默认 URL）
- URL 需要额外处理才能下载（如 QQ Linux 需先获取 cookie 再换取带 sign 的临时链接）

### 格式与变量

```bash
DLAGENTS=('protocol::command [options]')
```

`makepkg.conf(5)` 仅定义两个替换变量：

- `%u` - 替换为下载 URL
- `%o` - 替换为临时输出文件名（`<filename>.part`），脚本应写入此路径

> **注意**：`%d`、`%s` 等变量在 makepkg 7.x 中**不会被替换**，会作为字面值传给命令。常见误用 `%d` 引用脚本所在目录——`source=` 中的本地文件始终位于 PKGBUILD 同目录（`$startdir`），直接用相对路径即可。

### 常见陷阱

1. **命令必须使用绝对路径**（如 `/usr/bin/bash` 而非 `bash`）。makepkg 在解析 DLAGENTS 时不会查找 `$PATH`，使用相对名称会触发 `下载程序 xxx 没有安装` 错误。

2. **工作目录 = `$SRCDEST`**。makepkg 调用 DLAGENT 时 `pushd` 到 `$SRCDEST`（默认等于 `$startdir`）。引用 PKGBUILD 同目录下的脚本可直接用相对路径；若用户将 `SRCDEST` 指向其他目录，脚本应通过 `${BASH_SOURCE[0]}` 反查自身路径，或在 DLAGENTS 中使用绝对路径。

3. **不要在 DLAGENT 中嵌套 `${}` 变量**。`source_<arch>` 数组中不能使用 `${CARCH}`，DLAGENTS 同样在 `.SRCINFO` 展开时会被替换；硬编码所需的 URL、路径或脚本名。

### 示例：URL 签名（linuxqq-nt）

QQ 的 deb 包下载需先请求 `im.qq.com/index/` 获取 `tgw_l7_route` cookie，再调用 `GetSign` RPC 换取带 sign 的临时链接——直接请求 `qqdl.gtimg.cn` 上的原始 URL 会被拒绝。处理方式：编写专用脚本封装签名流程，DLAGENT 在下载前调用该脚本。

```bash
source=("${_pkgname}.sh" "linuxqq-get-url.sh")
source_x86_64=('https://qqdl.gtimg.cn/.../QQ_xxx_amd64_01.deb')
# ... 其他架构 ...

# 脚本约定两种调用模式：
#   1. 独立调用：linuxqq-get-url.sh <arch>            输出带 sign 的 URL
#   2. DLAGENT：  linuxqq-get-url.sh --dlagent <url> <output>  签名并写入 <output>
DLAGENTS=('https::/usr/bin/bash linuxqq-get-url.sh --dlagent %u %o')
```

### 参考

- `man 5 makepkg.conf` - DLAGENTS 官方定义
- [makepkg source code](https://gitlab.archlinux.org/pacman/pacman/-/tree/master/scripts/libmakepkg) - `source/file.sh` 的 `download_file()` 展示变量替换与 `.part` 重命名逻辑

## 图标安装 [推荐实践]

推荐使用 XDG hicolor 图标目录，而非传统的 `/usr/share/pixmaps/`：

```bash
install -Dm644 "icon.png" "${pkgdir}/usr/share/icons/hicolor/512x512/apps/${pkgname}.png"
```

### 文件名缓存冲突 [必须遵守]

当上游下载 URL 的文件名**不含版本号**时（如 `Trae-linux-x64.tar.gz`、`zen.linux-x86_64.tar.xz`），`makepkg` 在 `SRCDEST` 中会缓存旧文件。版本或内容更新后，文件名不变导致 `makepkg` 复用旧文件，新校验和不匹配，构建失败。

**必须**使用 `::` 别名为文件名添加 `${pkgver}-${pkgrel}`，确保每次更新都使用唯一文件名：

```bash
# ✓ 别名含版本和 pkgrel（每次更新文件名都不同）
source_x86_64=("Trae-linux-x64-${pkgver}-${pkgrel}.tar.gz::https://example.com/Trae-linux-x64.tar.gz")

# ✗ 无别名（文件名固定，缓存导致校验失败）
source_x86_64=('https://example.com/Trae-linux-x64.tar.gz')
```

**判断标准**：从 URL 提取文件名，如果文件名中不含版本号（如 `1.2.3`、`3.2.29_260528`），则必须添加别名。

`.desktop` 文件中 `Icon=` 字段只写图标名（不含扩展名），系统通过 hicolor 主题自动查找：

```ini
Icon=trae
```

上游 `.desktop` 文件的 `Icon=` 可能指向绝对路径或非标准名称，解包后必须修正：

```bash
sed -i 's|Icon=.*|Icon=navicat-icon|' "${pkgdir}/usr/share/applications/${pkgname}.desktop"
```

## Shell 补全 [推荐实践]

上游提供 bash/zsh 补全文件时，应安装到标准路径：

```bash
# bash
install -Dm644 "${pkgdir}/opt/${pkgname}/completions/bash/${pkgname}" \
    "${pkgdir}/usr/share/bash-completion/completions/${pkgname}"

# zsh
install -Dm644 "${pkgdir}/opt/${pkgname}/completions/zsh/_${pkgname}" \
    "${pkgdir}/usr/share/zsh/site-functions/_${pkgname}"
```

## provides 和 conflicts [推荐实践]

- `provides`：仅在包名与提供的虚拟包不同时声明；不要将 `pkgname` 加入，makepkg 自动处理
- `provides` 应附带版本号（如 `provides=('trae=2.3.25938')`），以便依赖特定版本的包正确解析
- `conflicts`：声明文件冲突或功能冲突的包
- `conflicts` 会同时匹配其他包的 `pkgname` 和 `provides`，因此变体包只需 `conflicts` 主包名即可阻止所有提供相同功能的包共存

```bash
# trae（主包，pkgname = trae，provides 自动包含）
conflicts=('trae-bin')

# trae-sg（变体包）
provides=('trae')
conflicts=('trae' 'trae-bin')
# conflicts 'trae' 同时阻止：主包 trae（pkgname 匹配）和 trae-us（provides 匹配）
```

---

## Electron 直装（tarball）

解压 tarball 后直接复制到 `/opt/`。

### source 文件排除 [项目约定]

makepkg 将 `source=()` 中的本地文件和下载的源码包以符号链接形式放入 `${srcdir}/`，与 tarball 解压内容混合。推荐按文件名模式显式排除：

```bash
for f in "${srcdir}"/*; do
    case "${f##*/}" in
        launcher.sh|app.desktop|*.tar.*) continue ;;
    esac
    cp -a "$f" "${pkgdir}/opt/${pkgname}/"
done
```

`*.tar.*` 排除源码包符号链接，避免包内出现指向 `$HOME/.cache/` 的悬空符号链接。

### SUID sandbox [项目约定]

部分 Electron/Chromium 发行版需要为 `chrome-sandbox` 设置 SUID 位：

```bash
chmod 4755 "${pkgdir}/opt/${pkgname}/chrome-sandbox"
```

即使 `cp -a` 保留了原始权限，仍显式设置作为防御性措施。现代 Chromium/Electron 可能使用 user namespace sandbox 替代 SUID。

**模式选择**：

- **无条件 chmod**（推荐用于稳定发布）：文件缺失时 makepkg 立即报错，便于排查上游变更：

```bash
chmod 4755 "${pkgdir}/opt/${pkgname}/chrome-sandbox"
```

- **防御性检查**（用于 nightly/twilight 等上游结构可能变化的场景）：文件不存在时输出警告而非静默跳过，避免运行时功能降级：

```bash
if [[ -f "${pkgdir}/opt/${pkgname}/chrome-sandbox" ]]; then
    chmod 4755 "${pkgdir}/opt/${pkgname}/chrome-sandbox"
else
    warning "SUID binary 'chrome-sandbox' not found; skipping"
fi
```

避免使用 `[[ -f ... ]] && chmod 4755 ...` 短路形式——文件缺失时完全静默，上游移除或重命名 SUID 二进制后用户无法诊断硬件加速降级的原因。

### 构建选项 [项目约定]

Electron 预编译二进制包使用 `!strip` 避免破坏符号表：

```bash
options=('!strip' '!debug')
```

### 启动脚本 [项目约定]

支持用户通过配置文件传递自定义参数：

```bash
#!/bin/bash
XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
if [[ -f "${XDG_CONFIG_HOME}/${pkgname}-flags.conf" ]]; then
    mapfile -t USER_FLAGS <<<"$(grep -v '^#' "${XDG_CONFIG_HOME}/${pkgname}-flags.conf")"
fi
exec /opt/${pkgname}/${binary} "${USER_FLAGS[@]}" "$@"
```

注意：参数展开中使用 `$HOME` 而非 `~`，因为 `~` 在引号内不会被展开。

**路径耦合风险**：启动脚本中的二进制路径（如 `/opt/${pkgname}/${binary}`）与 PKGBUILD 的 `_installdir` 存在隐式耦合。如果 PKGBUILD 修改了安装路径但未同步更新 launcher 脚本，构建不会报错但运行时静默失败（`No such file or directory`）。

建议在 PKGBUILD 中添加注释标注耦合关系：

```bash
# NOTE: launcher.sh hardcodes /opt/${pkgname}/${binary}
# If _installdir changes, the launcher script must also be updated.
install -Dm755 "${srcdir}/launcher.sh" "${pkgdir}/usr/bin/${pkgname}"
```

### 完整示例

```bash
package() {
    install -d "${pkgdir}/opt/${pkgname}"

    for f in "${srcdir}"/*; do
        case "${f##*/}" in
            launcher.sh|app.desktop|*.tar.*) continue ;;
        esac
        cp -a "$f" "${pkgdir}/opt/${pkgname}/"
    done

    chmod 4755 "${pkgdir}/opt/${pkgname}/chrome-sandbox"

    install -Dm755 "${srcdir}/launcher.sh" "${pkgdir}/usr/bin/${pkgname}"
    install -Dm644 "${srcdir}/app.desktop" "${pkgdir}/usr/share/applications/${pkgname}.desktop"
    install -Dm644 "${pkgdir}/opt/${pkgname}/resources/app/resources/linux/code.png" \
        "${pkgdir}/usr/share/icons/hicolor/512x512/apps/${pkgname}.png"

    # 许可证
    install -Dm644 "${pkgdir}/opt/${pkgname}/resources/app/LICENSE.txt" \
        "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"

    # Shell 补全
    install -Dm644 "${pkgdir}/opt/${pkgname}/resources/completions/bash/${pkgname}" \
        "${pkgdir}/usr/share/bash-completion/completions/${pkgname}"
    install -Dm644 "${pkgdir}/opt/${pkgname}/resources/completions/zsh/_${pkgname}" \
        "${pkgdir}/usr/share/zsh/site-functions/_${pkgname}"

    # 清理冗余文件
    rm -fv "${pkgdir}/opt/${pkgname}/resources/app/"*.dylib  # macOS 残留
    rm -rf "${pkgdir}/opt/${pkgname}/node_modules"           # 仅含类型定义
}
```

---

## deb 解包

使用 `bsdtar` 解包 deb 中的 `data.tar.xz`（或 `data.tar.gz`）到 `${pkgdir}/`，然后修正路径和清理冲突文件。

deb 文件是 ar 归档，makepkg 的 `bsdtar` 能直接处理（自动提取内层 data.tar.*）。`source` 声明示例：

```bash
source=("launcher.sh" "app.desktop")
source_x86_64=("https://example.com/${pkgname}_${pkgver}_amd64.deb")
source_aarch64=("https://example.com/${pkgname}_${pkgver}_arm64.deb")
```

### 内部结构 [推荐实践]

deb 包通常包含以下结构：

```
data.tar.xz
├── opt/<vendor>/              # 主程序（直接解压到目标位置）
├── usr/bin/                   # 启动脚本
├── usr/share/applications/    # .desktop 文件
└── usr/share/icons/           # 图标
```

`bsdtar -xf` 会将其中所有内容解压到 `${pkgdir}/`。Arch 官方规范要求文件不安装到 `/bin`、`/sbin` 等已合并目录，也不安装到 `/usr/local/`。deb 的 Debian 路径约定可能与 Arch 不一致（如 `/usr/lib/<package>/` vs `/usr/lib/`），解包后需要逐一检查。

### 解包与清理 [推荐实践]

```bash
package() {
    bsdtar -xf data.tar.xz -C "${pkgdir}/"

    # 修正 .desktop 文件中的路径和图标引用
    sed -i "s|Exec=.*|Exec=${pkgname}|" "${pkgdir}/usr/share/applications/${pkgname}.desktop"
    sed -i "s|Icon=.*|Icon=${pkgname}|" "${pkgdir}/usr/share/applications/${pkgname}.desktop"

    # 移除上游自带的启动脚本，使用自定义 launcher
    rm -f "${pkgdir}/usr/bin/${pkgname}"
    install -Dm755 "${srcdir}/launcher.sh" "${pkgdir}/usr/bin/${pkgname}"

    # 移除冲突的捆绑库
    rm -fv "${pkgdir}/opt/${pkgname}/lib/conflicting-lib.so"

    # 安装许可证
    install -Dm644 "${pkgdir}/opt/${pkgname}/LICENSE" \
        "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
}
```

### 捆绑库处理 [推荐实践]

deb 包常自带系统库的私有版本，可能与 Arch 系统库冲突。处理原则：

- 使用 `ldd` 和 `namcap`（或 `find-libdeps`）检查二进制实际依赖
- 与系统库版本冲突时，移除捆绑版本（如 `libssh2.so`、`libvips-cpp.so`）
- 仅在捆绑库是上游特有修改版本（非系统库的简单副本）时保留
- 移除前验证程序能正常启动

### 清理冗余文件 [推荐实践]

deb 包可能包含跨平台构建的残留文件：

```bash
# macOS 动态库（.dylib）不应出现在 Linux 包中
rm -fv "${pkgdir}/opt/${pkgname}/resources/app/"*.dylib
```

---

## AppImage 解包

在 `prepare()` 中使用 `--appimage-extract` 解包 squashfs，在 `package()` 中复制到 `/opt/`。

### 解包流程 [推荐实践]

```bash
prepare() {
    cd "${srcdir}/" && rm -rf "squashfs-root"
    chmod +x "${srcdir}/${_pkgname}.AppImage"
    "${srcdir}/${_pkgname}.AppImage" --appimage-extract
}

package() {
    install -d "${pkgdir}/opt/${_pkgname}"
    cp -a "${srcdir}/squashfs-root/." "${pkgdir}/opt/${_pkgname}/"

    ln -s "/opt/${_pkgname}/AppRun" "${pkgdir}/usr/bin/${pkgname}"

    install -Dm644 "${srcdir}/squashfs-root/usr/share/icons/hicolor/256x256/apps/app-icon.png" \
        "${pkgdir}/usr/share/icons/hicolor/256x256/apps/${pkgname}.png"

    install -Dm644 "${srcdir}/squashfs-root/app.desktop" \
        "${pkgdir}/usr/share/applications/${pkgname}.desktop"
    sed -i "s|Exec=.*|Exec=${pkgname}|" "${pkgdir}/usr/share/applications/${pkgname}.desktop"
    sed -i "s|Icon=.*|Icon=${pkgname}|" "${pkgdir}/usr/share/applications/${pkgname}.desktop"
}
```

### AppRun 启动问题 [推荐实践]

`AppRun` 可能依赖特定工作目录或环境变量。符号链接方式启动失败时，改用 wrapper script：

```bash
install -Dm755 "${srcdir}/launcher.sh" "${pkgdir}/usr/bin/${pkgname}"
```

wrapper script 中 `cd` 到 `/opt/${pkgname}/` 或设置必要环境变量后再执行 `AppRun`。

### 捆绑库冲突与 LD_PRELOAD [推荐实践]

AppImage 自带完整的运行时库，其中的某些库（如 `libsystemd.so`）可能与系统版本冲突，导致启动失败。解决方式：

- **方案一（推荐）**：移除冲突的捆绑库，让程序使用系统版本
- **方案二**：在 .desktop 的 `Exec=` 中添加 `env LD_PRELOAD=/usr/lib/libsystemd.so.0` 强制使用系统库

方案二适用于无法安全移除捆绑库的情况：

```bash
sed -i "s|Exec=${pkgname}|Exec=env LD_PRELOAD='/usr/lib/libsystemd.so.0' ${pkgname}|" \
    "${pkgdir}/usr/share/applications/${pkgname}.desktop"
```

### AppImage 依赖分析 [推荐实践]

AppImage 通常捆绑几乎所有运行时库（Qt、X11、curl、SSL 等），`depends` 只需列出**未捆绑的系统库**。分析步骤：

1. 使用 `find-libdeps *.pkg.tar.zst` 查看所有动态库依赖
2. 对比 AppImage 内 `usr/lib/` 下的捆绑库列表，排除已捆绑的
3. 只声明未捆绑的系统库

```bash
# AppImage 捆绑了 Qt6、X11、数据库驱动等，仅 fontconfig/freetype2 未捆绑
depends=('fontconfig' 'freetype2' 'hicolor-icon-theme')
```

不要将 `qt6-base` 等框架包列为依赖"代理"传递依赖——它们不会被实际加载，只会浪费磁盘空间。

### 清理冗余文件 [推荐实践]

AppImage 解包后通常包含上游构建环境的残留文件：

```bash
# Debian 版权文件（AppImage 从 Debian 环境构建）
rm -rf "${pkgdir}/opt/${_pkgname}/usr/share/doc"
```

---

## 源码编译

从源码编译安装，使用完整的 `prepare()` → `build()` → `check()` → `package()` 四阶段流程。

### 构建流程 [官方规范]

源码编译包与预编译包的核心区别：需要 `build()` 编译，通常包含 `check()` 测试，且需要声明 `makedepends` 和 `checkdepends`：

```bash
makedepends=('cmake' 'ninja')
checkdepends=('gtest')

prepare() {
    # 应用补丁等预处理
}

build() {
    # 编译
}

check() {
    # 运行测试
}

package() {
    # 安装到 pkgdir
}
```

各构建系统（Make/CMake/Meson/Go/Rust）的具体用法参考 [Arch Wiki](https://wiki.archlinux.org/title/Arch_package_guidelines)。

### 构建标志 [推荐实践]

`/etc/makepkg.conf` 提供标准构建标志（`CFLAGS`、`CXXFLAGS`、`LDFLAGS` 等），构建系统会自动读取。不应在 PKGBUILD 中硬编码编译优化参数。

安装时统一使用 `DESTDIR="${pkgdir}"`。

### strip 与 debug 包 [推荐实践]

源码编译的 ELF 二进制 strip 通常正常工作（与 Electron 预编译包不同），默认不需要 `!strip`。如需保留调试符号使用 `options=('!strip')`。

### VCS 包 [推荐实践]

从 Git/SVN 等版本控制系统直接构建时：

- `source` 使用 `git+https://...` 格式
- 必须实现 `pkgver()` 函数动态生成版本号
- 校验和使用 `SKIP`

```bash
pkgver() {
    cd "${srcdir}/${pkgname}"
    printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

source=("${pkgname}::git+https://github.com/user/repo.git")
sha256sums=('SKIP')
```
