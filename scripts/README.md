# AUR 包更新工具

一个用于自动更新 Arch Linux AUR 包的工具，支持从多个来源获取最新版本并更新 PKGBUILD 文件。

## 项目结构

```
scripts/
├── cli/                    # 命令行接口
│   ├── __init__.py
│   └── main.py            # 主入口点，处理命令行参数
├── core/                   # 核心功能
│   ├── __init__.py
│   └── package_updater.py # PackageUpdater类，整合所有功能
├── constants/              # 常量定义
│   ├── __init__.py
│   └── constants.py       # 枚举类和常量
├── fetcher/                # 数据获取
│   ├── __init__.py
│   └── fetcher.py         # Fetcher类，处理HTTP请求
├── loaders/                # 配置加载
│   ├── __init__.py
│   └── config_loader.py   # ConfigLoader类，加载YAML配置
├── parsers/                # 数据解析
│   ├── __init__.py
│   ├── base.py            # Parser基类
│   └── qq.py              # QQParser类，解析QQ版本信息
├── updater/                # 文件更新
│   ├── __init__.py
│   └── pkgbuild_editor.py # PKGBUILDEditor类，更新PKGBUILD文件
├── utils/                  # 工具函数
│   ├── __init__.py
│   └── hash.py             # 哈希计算相关函数
├── main.py                 # 程序入口点
├── packages.yaml           # 包配置文件
└── pyproject.toml          # 项目配置
```

## 模块职责

### cli

负责处理命令行接口，解析用户输入的参数，并调用核心功能。

### core

包含`PackageUpdater`类，整合了获取、解析和更新的完整流程。

### constants

定义项目中使用的枚举类和常量，如架构类型、包类型和哈希算法等。

### fetcher

负责从网络获取数据，提供基础的HTTP请求功能。

### loaders

负责加载和解析配置文件，提供包配置信息。

### parsers

负责解析不同来源的数据，提取版本信息和下载链接。

### updater

负责更新PKGBUILD文件，修改版本号、校验和等字段。

### utils

提供通用工具函数，如哈希计算等。

## 使用方法

### 更新所有包

```bash
python main.py --all
```

### 更新指定包

```bash
python main.py --package qq
```

### 列出所有可用包

```bash
python main.py --list
```

## 依赖

- Python >= 3.13
- httpx >= 0.28.1
- pydantic >= 2.12.5
- pyyaml >= 6.0.3
- pathlib
- argparse >= 1.4.0

## 配置

包配置存储在`packages.yaml`文件中，每个包包含以下信息：

- name: 包名
- source: 来源类型
- fetch_url: 获取信息的URL
- upstream: 上游项目URL
- parser: 使用的解析器
- pkgbuild: PKGBUILD文件路径

## 添加新的软件包

要添加新的软件包，需要：

1. 在`packages.yaml`中添加配置
2. 在`parsers`目录中创建相应的解析器类
3. 确保解析器实现了`parse_version`和`parse_deb_url`方法

## 支持的架构

- x86_64
- aarch64
- loong64

## 支持的哈希算法

- SHA256
- SHA512
