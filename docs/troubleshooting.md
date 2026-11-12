# AUR 包已知问题

按包列出各包在 Arch Linux 上的已知问题及处理方式。

---

## Trae 系列（trae / trae-sg / trae-us / trae-cn）

### 捆绑 GCC 运行时库导致 ckg 索引崩溃

**路径**：`resources/app/modules/ckg/binary/`

上游为 Ubuntu 打包，捆绑了 GCC 运行时库 `libstdc++.so.6` 和 `libgcc_s.so.1`。这些库通过 `start.sh` 的 `LD_LIBRARY_PATH` 优先加载，与 Arch 的 `gcc-libs` 产生 ABI 冲突，导致 ckg 进程启动即崩溃（exit code 256），项目索引功能完全失效。

**处理**：`package()` 中删除这两个文件，ckg 回退使用系统 `gcc-libs`（`libstdc++` 向后兼容）。其他捆绑库（`libzmq`、`libsodium`、`libpgm`）保留，可能是上游定制构建。

### makepkg 缓存冲突

上游下载 URL 文件名不含版本号（如 `Trae-linux-x64.tar.gz`、`Trae_CN-linux-x64.tar.gz`），makepkg 在 `SRCDEST` 中缓存旧文件，版本更新后校验和不匹配。

**处理**：`source` 声明中使用 `::` 别名添加 `${pkgver}-${pkgrel}`。

### tarball 内包含冗余文件

解压后包含 GPG 签名文件（`.asc`）、Windows 批处理文件（`.bat`）、构建系统日志（`rush-logs/`），增加包体积。

**处理**：`package()` 末尾统一清理。

---

## Navicat（navicat17-premium-zh-cn）

### 捆绑 libsystemd 与系统 libmount 不兼容

Navicat AppImage 捆绑了自己的 `libsystemd.so`，但运行时链接系统的 `libmount.so`（来自 `util-linux`）。两个库之间存在版本耦合，混合使用导致运行时错误。

**处理**：启动脚本 `navicat.sh` 通过 `LD_PRELOAD` 强制优先加载系统的 `libsystemd.so.0`：

```bash
export LD_PRELOAD="/usr/lib/libsystemd.so.0${LD_PRELOAD:+:$LD_PRELOAD}"
```

---

## 通用

### 修改本地源文件后 hash 不匹配

本地源文件（`.sh`、`.desktop`、`.install`）列入 `source=()` 数组，makepkg 会校验其哈希。修改文件内容但未更新 PKGBUILD 中对应的校验和（如 `b2sums`、`sha512sums`）会导致构建失败。

**处理**：修改本地源文件后必须同步更新 PKGBUILD 中对应的校验和。

### deb 数据层压缩格式不固定

makepkg 解包 deb 后，数据层文件名由上游决定：多数包是 `data.tar.xz`，也有用 `data.tar.gz` 的（如 rustmusic）。在 `package()` 里写死 `data.tar.xz` 会在后一类包上构建失败。

**处理**：先 `bsdtar -tf <deb>` 确认实际文件名，再在 `package()` 中对应解包。仅支持单一格式的包，可参考 `structure/<pkgname>.txt` 快照确认。
