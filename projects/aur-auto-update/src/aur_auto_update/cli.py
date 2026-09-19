"""AUR 包自动更新工具命令行入口"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from aur_auto_update.core.package_updater import PackageUpdater


def _configure_logging() -> None:
    """配置日志格式"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


async def _dispatch(args: argparse.Namespace) -> int:
    """按命令行参数执行对应操作，确保资源在退出前释放"""
    updater = PackageUpdater(args.config)

    try:
        # 列出所有包
        if args.list:
            updater.list_available_packages()
            return 0

        # 更新指定的包
        if args.package:
            success_count, total_count = await updater.update_packages(args.package)
            if total_count > 0 and success_count == 0:
                return 1
            return 0

        # 更新所有包
        success_count, total_count = await updater.update_all_packages()
        if total_count > 0 and success_count == 0:
            return 1
        return 0
    finally:
        await updater.close()


def main() -> int:
    """CLI 入口，处理命令行参数并执行相应操作"""
    _configure_logging()

    parser = argparse.ArgumentParser(description="AUR包更新工具")
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=Path("config.yaml"),
        help="配置文件路径（默认 config.yaml，相对当前目录；配置内的相对路径以配置文件所在目录为基准）",
    )
    parser.add_argument(
        "--package", "-p", nargs="+", metavar="NAME", help="更新指定的包（可指定多个）"
    )
    parser.add_argument("--list", "-l", action="store_true", help="列出所有可用的包")
    parser.add_argument("--all", "-a", action="store_true", help="更新所有包")

    args = parser.parse_args()

    return asyncio.run(_dispatch(args))
