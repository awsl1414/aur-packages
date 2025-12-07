#!/usr/bin/env python3
"""
AUR包更新工具主入口
"""

import argparse
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core import PackageUpdater


async def update_main():
    """主函数，使用argparse处理命令行参数"""
    parser = argparse.ArgumentParser(description="AUR包更新工具")
    parser.add_argument("--package", "-p", help="更新指定的包")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有可用的包")
    parser.add_argument("--all", "-a", action="store_true", help="更新所有包")

    args = parser.parse_args()

    updater = PackageUpdater()

    if args.list:
        updater.list_available_packages()
        return

    if args.package:
        success = await updater.update_single_package(args.package)
        sys.exit(0 if success else 1)
    elif args.all:
        await updater.update_all_packages()
    else:
        # 默认行为：更新所有包
        await updater.update_all_packages()


def main():
    """主函数"""
    print("AUR包更新工具")
    print("=" * 50)

    # 运行更新主程序
    asyncio.run(update_main())


if __name__ == "__main__":
    main()
