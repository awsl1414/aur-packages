"""
包更新器
整合fetch、parse和update三个流程

架构设计：
1. 并行更新所有维护的 AUR 包（使用 asyncio.gather）
2. 并行下载单个包的所有架构（使用 Downloader 的并发功能）
"""

import asyncio
import logging
from functools import partial
from pathlib import Path

from constants.constants import DOWNLOAD_DIR, ArchEnum, HashAlgorithmEnum, ParserEnum
from fetcher.fetcher import Fetcher
from loaders.config_loader import ConfigLoader, PackageConfig
from parsers.base_parser import BaseParser
from parsers.navicat import NavicatPremiumCSParser
from parsers.pypi import PyPIParser
from parsers.qq import QQParser
from parsers.trae import TraeParser, TraeRegion
from parsers.zen import ZenParser
from updater.pkgbuild_editor import PKGBUILDEditor
from utils.downloader import Downloader
from utils.hash import calculate_file_hash
from utils.url_utils import generate_download_filename
from utils.version_utils import compare_versions

logger = logging.getLogger(__name__)


class PackageUpdater:
    """包更新器，整合fetch、parse和update流程"""

    def __init__(self) -> None:
        # 加载配置
        self.config = ConfigLoader.load_from_yaml()

        # 从配置中获取下载设置
        download_settings = self.config.settings.download

        # 初始化 Fetcher（使用配置的超时时间）
        self.fetcher = Fetcher(timeout=download_settings.timeout)

        # 注册解析器
        navicat_config = self.config.packages.get("navicat")
        navicat_urls = navicat_config.urls if navicat_config else {}
        self.parsers: dict[str, BaseParser] = {
            ParserEnum.QQ.value: QQParser(),
            ParserEnum.NAVICAT_PREMIUM_CS.value: NavicatPremiumCSParser(
                urls=navicat_urls
            ),
            ParserEnum.TRAE.value: TraeParser(),
            ParserEnum.TRAE_SG.value: TraeParser(region=TraeRegion.SG),
            ParserEnum.TRAE_US.value: TraeParser(region=TraeRegion.US),
            ParserEnum.TRAE_CN.value: TraeParser(region=TraeRegion.CN),
            ParserEnum.ZEN.value: ZenParser(),
            ParserEnum.BT_DUALBOOT.value: PyPIParser(package_name="bt-dualboot-ng"),
        }

        # 初始化下载器（使用配置的下载设置）
        self.downloader = Downloader(
            max_retries=download_settings.max_retries,
            retry_wait=download_settings.retry_wait,
            timeout=download_settings.timeout,
            connections=download_settings.connections,
            show_progress=download_settings.show_progress,
        )

        # 项目根目录指仓库根目录（aur-packages/），config.yaml 中的
        # packages/xxx/PKGBUILD 路径即相对于此处。当前脚本位于 scripts/core/，
        # 需要向上三级到达仓库根目录
        self.project_root = Path(__file__).parent.parent.parent
        # PKGBUILD 目录相对于项目根目录
        self.pkgbuild_root = self.project_root

    async def close(self) -> None:
        """释放资源"""
        await self.fetcher.client.aclose()

    def _get_pkgbuild_path(self, pkgbuild_relative_path: str) -> Path:
        """
        获取PKGBUILD文件的完整路径

        相对路径以仓库根目录（self.pkgbuild_root）为基准解析，
        与 config.yaml 中 packages/xxx/PKGBUILD 的写法一致。

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

    def _check_pkgbuild_exists(
        self, package_name: str, package_config: PackageConfig
    ) -> bool:
        """
        检查 PKGBUILD 文件是否存在

        Args:
            package_name: 包名
            package_config: 包配置

        Returns:
            True 如果文件存在，False 否则
        """
        pkgbuild_path = self._get_pkgbuild_path(package_config.pkgbuild)
        if not pkgbuild_path.exists():
            logger.warning("  跳过: PKGBUILD 文件不存在: %s", pkgbuild_path)
            return False
        return True

    def _fetch_arch_urls(
        self, parser: BaseParser, supported_archs: list[ArchEnum], response_data: str
    ) -> dict[str, str]:
        """获取所有架构的下载 URL"""
        arch_urls = {}
        for arch in supported_archs:
            url = parser.parse_url(arch, response_data)
            if url:
                arch_urls[arch.value] = url
            else:
                logger.warning("无法获取 %s 架构的下载URL", arch.value)
        return arch_urls

    async def _download_and_verify(
        self,
        package_name: str,
        new_version: str,
        arch_urls: dict[str, str],
        hash_algorithm: str = HashAlgorithmEnum.B2.value,
        verify_only: bool = False,
    ) -> tuple[dict[str, str], bool]:
        """
        下载文件并计算校验和

        使用 Downloader 的并发下载功能，并行下载单个包的所有架构
        """
        download_dir = Path(DOWNLOAD_DIR)
        download_dir.mkdir(exist_ok=True)

        downloads = {
            arch: (
                url,
                download_dir
                / generate_download_filename(
                    package_name, new_version, arch, url, default_extension=".deb"
                ),
            )
            for arch, url in arch_urls.items()
        }

        # 使用 Downloader 并行下载所有架构
        download_results = await self.downloader.download_all(
            downloads, package_name=package_name
        )

        checksums = {}
        failed_archs = []

        for arch, result in download_results.items():
            if not result.success:
                if not verify_only:
                    logger.error("  错误: %s 架构下载失败: %s", arch, result.error)
                    failed_archs.append(arch)
                else:
                    logger.warning("  警告: %s 架构下载失败: %s", arch, result.error)
                continue

            if result.file_path is None:
                if not verify_only:
                    logger.error("  错误: %s 架构文件路径为空", arch)
                    failed_archs.append(arch)
                continue

            checksum = await self._calculate_checksum(result.file_path, hash_algorithm)
            checksums[arch] = checksum
            logger.info("  %s 架构哈希验证通过: %s", arch, checksum)

        if not verify_only and (failed_archs or not checksums):
            if failed_archs:
                logger.error(
                    "  错误: %d 个架构下载失败: %s", len(failed_archs), failed_archs
                )
            if not checksums:
                logger.error("  错误: 没有成功下载任何架构的文件")
            return {}, False

        return checksums, True

    async def update_package(
        self, package_name: str, package_config: PackageConfig
    ) -> bool:
        """更新单个包"""
        logger.info("开始更新包: %s", package_name)

        try:
            # 1. 获取最新版本信息
            logger.info("  1. 从 %s 获取版本信息...", package_config.fetch_url)
            response_data = await self.fetcher.fetch_text(package_config.fetch_url)
            if not response_data:
                logger.error("  错误: 无法获取版本信息")
                return False

            # 2. 解析版本号和下载 URL
            logger.info("  2. 解析版本信息...")
            parser = self.parsers.get(package_config.parser)
            if not parser:
                logger.error("  错误: 找不到解析器 %s", package_config.parser)
                return False

            new_version = parser.parse_version(response_data)
            if not new_version:
                logger.error("  错误: 无法解析版本号")
                return False

            logger.info("  最新版本: %s", new_version)

            # 3. 检查当前版本
            pkgbuild_path = self._get_pkgbuild_path(package_config.pkgbuild)
            logger.info("  PKGBUILD路径: %s", pkgbuild_path)

            if not pkgbuild_path.exists():
                logger.error("  错误: PKGBUILD文件不存在: %s", pkgbuild_path)
                return False

            editor = PKGBUILDEditor(pkgbuild_path)
            current_version = editor.get_pkgver()
            logger.info("  当前版本: %s", current_version)

            # 获取包支持的架构
            supported_archs = package_config.get_supported_archs()

            # 获取生效的哈希算法（包级覆盖 > 全局默认）
            hash_algorithm = package_config.get_effective_hash_algorithm(
                self.config.settings.hash_algorithm
            )

            # 版本比较
            version_comparison = compare_versions(new_version, current_version)

            if version_comparison <= 0:
                # 当前版本 >= 新版本，仅验证哈希
                return await self._handle_version_not_newer(
                    package_name,
                    new_version,
                    current_version,
                    version_comparison,
                    parser,
                    supported_archs,
                    response_data,
                    hash_algorithm,
                )

            # 版本更新流程
            return await self._handle_version_update(
                package_name,
                new_version,
                current_version,
                editor,
                parser,
                supported_archs,
                response_data,
                package_config,
                hash_algorithm,
            )

        except Exception:
            logger.exception("更新包 %s 时发生异常", package_name)
            return False

    async def _handle_version_not_newer(
        self,
        package_name: str,
        new_version: str,
        current_version: str,
        version_comparison: int,
        parser: BaseParser,
        supported_archs: list[ArchEnum],
        response_data: str,
        hash_algorithm: str = HashAlgorithmEnum.B2.value,
    ) -> bool:
        """
        处理版本不更新的情况（当前版本 >= 新版本）

        两种场景：
        1. 当前版本 > 新版本：版本降级，仅验证哈希
        2. 当前版本 = 新版本：版本相同，检查哈希变化并更新 pkgrel
        """
        if version_comparison < 0:
            # 当前版本 > 新版本：版本降级
            logger.info(
                "  跳过更新: 新版本 %s 低于当前版本 %s", new_version, current_version
            )
            logger.info("  说明: 当前包版本较新，无需降级")
            logger.info("  注意: 仍将下载并验证哈希数据...")

            arch_urls = self._fetch_arch_urls(parser, supported_archs, response_data)
            if not arch_urls:
                logger.error("  错误: 无法获取任何架构的下载URL")
                return False

            checksums, _ = await self._download_and_verify(
                package_name, new_version, arch_urls, hash_algorithm, verify_only=True
            )

            logger.info("  包 %s 验证完成（未更新 PKGBUILD）", package_name)
            return True

        # 当前版本 = 新版本：检查哈希变化
        logger.info("  版本未变化，检查文件哈希是否变化...")

        # 获取当前 PKGBUILD 中的哈希值
        pkgbuild_path = self._get_pkgbuild_path(
            self.config.packages[package_name].pkgbuild
        )
        editor = PKGBUILDEditor(pkgbuild_path)

        current_checksums = {}
        for arch in supported_archs:
            # ANY 架构使用非架构特定字段 sums=()，其余使用 sums_<arch>=()
            field_arch = None if arch == ArchEnum.ANY else arch.value
            current_checksum = editor.get_checksum(
                arch=field_arch, hash_algorithm=hash_algorithm
            )
            if current_checksum:
                current_checksums[arch.value] = current_checksum
            else:
                logger.warning("  警告: 无法获取 %s 架构的当前哈希值", arch.value)

        # 下载并计算新哈希值
        arch_urls = self._fetch_arch_urls(parser, supported_archs, response_data)
        if not arch_urls:
            logger.error("  错误: 无法获取任何架构的下载URL")
            return False

        new_checksums, success = await self._download_and_verify(
            package_name, new_version, arch_urls, hash_algorithm
        )
        if not success:
            return False

        # 比较哈希值
        hash_changed = False
        for arch, new_checksum in new_checksums.items():
            if arch in current_checksums:
                if current_checksums[arch] != new_checksum:
                    logger.info("  检测到 %s 架构的文件哈希已变化", arch)
                    hash_changed = True
                else:
                    logger.info("  %s 架构的文件哈希未变化", arch)

        if not hash_changed:
            logger.info("  所有架构的文件哈希均未变化，无需更新")
            return True

        # 哈希已变化，自增 pkgrel
        logger.info("  文件哈希已变化，更新 pkgrel 和校验和...")
        current_pkgrel = editor.get_pkgrel()
        new_pkgrel = current_pkgrel + 1
        logger.info("  pkgrel: %d → %d", current_pkgrel, new_pkgrel)

        editor.update_pkgrel(new_pkgrel)

        # 更新校验和（不更新 source URL，因为版本未变）
        for arch_value, checksum in new_checksums.items():
            field_arch = None if arch_value == ArchEnum.ANY.value else arch_value
            editor.update_checksum(checksum, hash_algorithm, arch=field_arch)

        editor.save()
        logger.info("  包 %s 的 pkgrel 已更新（版本未变但哈希已变）", package_name)
        return True

    async def _handle_version_update(
        self,
        package_name: str,
        new_version: str,
        current_version: str,
        editor: PKGBUILDEditor,
        parser: BaseParser,
        supported_archs: list[ArchEnum],
        response_data: str,
        package_config: PackageConfig,
        hash_algorithm: str = HashAlgorithmEnum.B2.value,
    ) -> bool:
        """处理版本更新流程"""
        logger.info("  3. 下载文件并计算校验和...")
        logger.info("  支持的架构: %s", [arch.value for arch in supported_archs])

        arch_urls = self._fetch_arch_urls(parser, supported_archs, response_data)
        if not arch_urls:
            logger.error("  错误: 无法获取任何架构的下载URL")
            return False

        checksums, success = await self._download_and_verify(
            package_name, new_version, arch_urls, hash_algorithm
        )
        if not success:
            return False

        # 更新 PKGBUILD
        logger.info("  4. 更新 PKGBUILD 版本和校验和...")
        editor.update_pkgver(new_version)
        editor.update_pkgrel(1)  # 重置 pkgrel 为 1

        # 更新 source 和校验和；ANY 架构用非架构特定字段，其余用架构特定字段
        for arch_value, url in arch_urls.items():
            field_arch = None if arch_value == ArchEnum.ANY.value else arch_value
            if package_config.update_source_url:
                editor.update_source(url, arch=field_arch)
            editor.update_checksum(
                checksums[arch_value], hash_algorithm, arch=field_arch
            )

        editor.save()
        logger.info("  5. PKGBUILD 已更新")

        logger.info("包 %s 更新完成!", package_name)
        return True

    async def _calculate_checksum(self, file_path: Path, hash_algorithm: str) -> str:
        """计算文件校验和"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            partial(calculate_file_hash, file_path, hash_algorithm),
        )

    async def update_all_packages(self) -> tuple[int, int]:
        """
        并行更新所有配置的包

        所有包同时进入更新流程，每个包的多个架构并行下载

        Returns:
            (成功数量, 总数量)
        """
        # 过滤出启用的包
        enabled_packages = {
            name: config
            for name, config in self.config.packages.items()
            if config.enable
        }
        disabled_packages = [
            name for name, config in self.config.packages.items() if not config.enable
        ]

        logger.info(
            "开始更新所有包（共 %d 个启用，%d 个禁用）...",
            len(enabled_packages),
            len(disabled_packages),
        )

        if disabled_packages:
            logger.info("  已跳过禁用的包: %s", ", ".join(disabled_packages))

        # 预检查 PKGBUILD 文件是否存在
        valid_packages = {}
        missing_pkgbuild_packages = []

        for package_name, package_config in enabled_packages.items():
            if not self._check_pkgbuild_exists(package_name, package_config):
                missing_pkgbuild_packages.append(package_name)
            else:
                valid_packages[package_name] = package_config

        if missing_pkgbuild_packages:
            logger.info(
                "  已跳过 PKGBUILD 文件不存在的包: %s",
                ", ".join(missing_pkgbuild_packages),
            )

        if not valid_packages:
            logger.info("\n没有可更新的包")
            return 0, 0

        return await self._run_updates(valid_packages)

    def _is_package_updatable(
        self, package_name: str, package_config: PackageConfig
    ) -> tuple[bool, str | None]:
        """
        检查包是否可更新

        Args:
            package_name: 包名
            package_config: 包配置

        Returns:
            (是否可更新, 跳过原因)
        """
        if not package_config.enable:
            return False, f"包 '{package_name}' 已禁用"

        if not self._check_pkgbuild_exists(package_name, package_config):
            return False, f"包 '{package_name}' PKGBUILD 文件不存在"

        return True, None

    async def _run_updates(
        self, valid_packages: dict[str, PackageConfig]
    ) -> tuple[int, int]:
        """并行更新 valid_packages 中的包，返回 (成功数, 总数)"""
        tasks = [
            self.update_package(name, config)
            for name, config in valid_packages.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        success_count = sum(1 for r in results if r is True)
        logger.info("")
        logger.info("更新完成: %d/%d 个包更新成功", success_count, len(valid_packages))
        return success_count, len(valid_packages)

    async def update_packages(self, package_names: list[str]) -> tuple[int, int]:
        """
        更新指定的包列表

        Args:
            package_names: 包名列表

        Returns:
            (成功数量, 总数量)
        """
        if not package_names:
            return 0, 0

        # 验证和过滤包
        valid_packages: dict[str, PackageConfig] = {}
        invalid_packages: list[str] = []
        skip_reasons: list[str] = []

        for package_name in package_names:
            if package_name not in self.config.packages:
                invalid_packages.append(package_name)
                continue

            package_config = self.config.packages[package_name]
            is_updatable, skip_reason = self._is_package_updatable(
                package_name, package_config
            )

            if is_updatable:
                valid_packages[package_name] = package_config
            elif skip_reason:
                skip_reasons.append(skip_reason)

        # 输出跳过的包
        if invalid_packages:
            logger.error("错误: 以下包不在配置中: %s", ", ".join(invalid_packages))

        for reason in skip_reasons:
            logger.info("  跳过: %s", reason)

        if not valid_packages:
            return 0, 0

        # 并行更新包
        logger.info("开始更新 %d 个包...", len(valid_packages))

        return await self._run_updates(valid_packages)

    def list_available_packages(self) -> None:
        """列出所有可用的包"""
        logger.info("可用的包:")
        for package_name, package_config in self.config.packages.items():
            status = "启用" if package_config.enable else "禁用"
            logger.info("  - %s [%s]", package_name, status)
