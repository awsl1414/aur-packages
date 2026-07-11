# structure/

各软件包**解包后的目录结构快照**（文本），用 `tree` 提取，供分析参考。不存储源文件本身。

## 用途

- 快速定位上游包内文件位置（如 `libcc.so`、`.desktop`、图标路径），无需重新解包 717M 的 AppImage
- 对比版本间目录结构变化
- 排查打包/运行时问题时对照原始结构

## 命名

`<pkgname>.txt`，与 `packages/<pkgname>` 对应。例如：

```
structure/
├── README.md
└── navicat17-premium-zh-cn.txt
```

## 添加新包快照

解包上游包后（AppImage 用 `--appimage-extract`、tarball 用 `tar -xf`、deb 用 `bsdtar -xf`），在解包根的父目录执行：

```bash
tree -aF <解包根目录> > structure/<pkgname>.txt
```

建议在文件顶部以 `#` 注释标注：来源包与版本、提取命令、架构说明、日期。
