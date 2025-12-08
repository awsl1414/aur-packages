#!/usr/bin/env python3
"""
包更新器
整合fetch、parse和update三个流程
"""

from pathlib import Path

from constants import DOWNLOAD_DIR, ParserEnum
from fetcher import Fetcher
from loaders import ConfigLoader, PackageConfig
from parsers import QQParser
from updater import PKGBUILDEditor


class PackageUpdater:
    """包更新器，整合fetch、parse和update流程"""

    def __init__(self):
        self.fetcher = Fetcher()
        self.config = ConfigLoader.load_from_yaml()
        self.parsers = {
            ParserEnum.QQ.value: QQParser(),
        }
        # 获取项目根目录（这里的项目根目录指更新脚本的根目录）
        # 当前脚本位于 scripts/core/，所以需要向上两级到达项目根目录
        self.project_root = Path(__file__).parent.parent
        # PKGBUILD目录相对于项目根目录
        self.pkgbuild_root = self.project_root.parent

    def _get_pkgbuild_path(self, pkgbuild_relative_path: str) -> Path:
        """
        获取PKGBUILD文件的完整路径

        注意：PKGBUILD目录需要从项目根目录的上级目录开始

        Args:
            pkgbuild_relative_path: PKGBUILD的相对路径

        Returns:
            PKGBUILD的完整路径
        """
        # 如果路径已经是绝对路径，直接返回
        pkgbuild_path = Path(pkgbuild_relative_path)
        if pkgbuild_path.is_absolute():
            return pkgbuild_path

        # 否则，将其与pkgbuild_root结合
        full_path = self.pkgbuild_root / pkgbuild_relative_path
        return full_path

    async def update_package(
        self, package_name: str, package_config: PackageConfig
    ) -> bool:
        """
        更新单个包

        Args:
            package_name: 包名
            package_config: 包配置

        Returns:
            更新是否成功
        """
        print(f"开始更新包: {package_name}")

        try:
            # 1. Fetch阶段：获取最新版本信息
            print(f"  1. 从 {package_config.fetch_url} 获取版本信息...")
            response_data = await self.fetcher.fetch_text(package_config.fetch_url)
            if not response_data:
                print(f"  错误: 无法获取版本信息")
                return False

            # 2. Parse阶段：解析版本号和下载URL
            print(f"  2. 解析版本信息...")
            parser = self.parsers.get(package_config.parser)
            if not parser:
                print(f"  错误: 找不到解析器 {package_config.parser}")
                return False

            new_version = parser.parse_version(response_data)
            if not new_version:
                print(f"  错误: 无法解析版本号")
                return False

            print(f"  最新版本: {new_version}")

            # 3. 检查当前版本
            # 使用_get_pkgbuild_path方法获取正确的PKGBUILD路径
            pkgbuild_path = self._get_pkgbuild_path(package_config.pkgbuild)
            print(f"  PKGBUILD路径: {pkgbuild_path}")

            if not pkgbuild_path.exists():
                print(f"  错误: PKGBUILD文件不存在: {pkgbuild_path}")
                return False

            editor = PKGBUILDEditor(pkgbuild_path)
            current_version = editor.get_pkgver()
            print(f"  当前版本: {current_version}")

            if new_version == current_version:
                print(f"  版本已是最新，无需更新")
                return True

            # 4. 下载文件并计算校验和
            print(f"  3. 下载文件并计算校验和...")
            download_dir = Path(DOWNLOAD_DIR)
            download_dir.mkdir(exist_ok=True)

            # 获取包支持的架构
            supported_archs = package_config.get_supported_archs()
            print(f"  支持的架构: {[arch.value for arch in supported_archs]}")

            # 获取各架构的下载URL
            arch_urls = {}
            for arch in supported_archs:
                url = parser.parse_deb_url(arch, response_data)
                if url:
                    arch_urls[arch.value] = url
                    print(f"  {arch.value} 架构下载URL: {url}")
                else:
                    print(f"  警告: 无法获取 {arch.value} 架构的下载URL")

            if not arch_urls:
                print(f"  错误: 无法获取任何架构的下载URL")
                return False

            # 下载各架构的文件并计算校验和
            arch_checksums = {}
            for arch, url in arch_urls.items():
                filename = f"{package_name}_{new_version}_{arch}.deb"
                file_path = download_dir / filename

                print(f"    下载 {arch} 架构文件: {url}")
                if not await self._download_file(url, file_path):
                    print(f"    错误: 下载 {arch} 架构文件失败")
                    return False

                # 计算校验和
                checksum = await self._calculate_checksum(file_path)
                arch_checksums[arch] = checksum
                print(f"    {arch} 架构校验和: {checksum}")

            # 5. 更新PKGBUILD
            print(f"  4. 更新PKGBUILD...")
            editor.update_pkgver(new_version)
            editor.update_pkgrel(1)  # 重置pkgrel为1

            # 更新各架构的source和校验和
            for arch, url in arch_urls.items():
                editor.update_source_url(arch, url)
                editor.update_arch_checksum(arch, arch_checksums[arch])

            # 保存PKGBUILD
            editor.save()
            print(f"  5. PKGBUILD已更新")

            print(f"包 {package_name} 更新完成!")
            return True

        except Exception as e:
            print(f"  错误: 更新包 {package_name} 时发生异常: {e}")
            return False

    async def _download_file(self, url: str, file_path: Path) -> bool:
        """
        下载文件

        Args:
            url: 下载URL
            file_path: 保存路径

        Returns:
            下载是否成功
        """
        try:
            response = await self.fetcher.client.get(url)
            response.raise_for_status()

            with open(file_path, "wb") as f:
                f.write(response.content)

            return True
        except Exception as e:
            print(f"下载文件失败: {e}")
            return False

    async def _calculate_checksum(self, file_path: Path) -> str:
        """
        计算文件的校验和

        Args:
            file_path: 文件路径

        Returns:
            SHA512校验和
        """
        from utils import calculate_file_hash
        from constants import HashAlgorithmEnum

        return calculate_file_hash(file_path, HashAlgorithmEnum.SHA512.value)

    async def update_all_packages(self) -> None:
        """更新所有配置的包"""
        print("开始更新所有包...")

        success_count = 0
        total_count = len(self.config.packages)

        for package_name, package_config in self.config.packages.items():
            print()
            success = await self.update_package(package_name, package_config)
            if success:
                success_count += 1

        print()
        print(f"更新完成: {success_count}/{total_count} 个包更新成功")

    async def update_single_package(self, package_name: str) -> bool:
        """
        更新单个指定的包

        Args:
            package_name: 要更新的包名

        Returns:
            更新是否成功
        """
        if package_name not in self.config.packages:
            print(f"错误: 包 '{package_name}' 不在配置中")
            return False

        package_config = self.config.packages[package_name]
        return await self.update_package(package_name, package_config)

    def list_available_packages(self) -> None:
        """列出所有可用的包"""
        print("可用的包:")
        for package_name in self.config.packages.keys():
            print(f"  - {package_name}")
