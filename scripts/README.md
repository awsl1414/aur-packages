# scripts/

AUR 包自动更新工具的核心代码目录。完整项目文档见根目录 [CLAUDE.md](../CLAUDE.md)。

uv 项目根位于仓库根目录（`pyproject.toml`、`uv.lock`、`config.yaml` 均在仓库根），本目录仅存放 Python 源码。所有命令在仓库根目录执行。

## 模块结构

```
scripts/
├── core/           # 核心协调器（PackageUpdater：Fetch → Parse → Update）
├── constants/      # 枚举定义（ArchEnum, ParserEnum, HashAlgorithmEnum）
├── fetcher/        # HTTP 客户端（httpx，获取版本信息）
├── loaders/        # 配置加载（仓库根 config.yaml → Pydantic 模型）
├── parsers/        # 版本解析器（BaseParser 及子类）
├── updater/        # PKGBUILD 编辑器（正则替换）
├── utils/          # 工具函数（aria2c 下载器、哈希、URL/版本工具）
├── tests/          # pytest 测试
└── main.py         # 程序入口（argparse 命令行接口）
```

## 前置依赖

- Python >= 3.13
- aria2c（用于多线程下载）
- uv（包管理器）
