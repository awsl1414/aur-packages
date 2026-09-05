"""
包更新器
整合fetch、parse和update三个流程

架构设计：
1. 并行更新所有维护的 AUR 包（使用 asyncio.gather）
2. 所有上游解析统一由 aur-packages-helper 的 API 完成，客户端只消费
   {version, urls, hashes} 结构
3. helper 未提供 hashes（或部分架构缺失）时，回退到按 urls 下载 + 本地计算
"""

import asyncio
import logging
from functools import partial
from pathlib import Path

from constants.constants import ArchEnum, HashAlgorithmEnum
from fetcher.fetcher import Fetcher
from loaders.config_loader import ConfigLoader, PackageConfig
from parsers.api_parser import ApiParser, ParsedPackage
from updater.pkgbuild_editor import PKGBUILDEditor
from utils.downloader import Downloader
from utils.hash import calculate_file_hash
from utils.url_utils import generate_download_filename
from utils.version_utils import compare_versions

logger = logging.getLogger(__name__)

# 回退下载目录（helper 未提供 hashes 时本地下载计算）
DOWNLOAD_DIR = "downloads"


class PackageUpdater:
    """包更新器，整合fetch、parse和update流程"""

    def __init__(self) -> None:
        # 加载配置
        self.config = ConfigLoader.load_from_yaml()

        # 从配置中获取下载设置
        download_settings = self.config.settings.download

        # 初始化 Fetcher（复用下载设置的超时与重试参数；helper API 的
        # 429/5xx 瞬时错误由 Fetcher 指数退避重试）
        self.fetcher = Fetcher(
            timeout=download_settings.timeout,
            max_retries=download_settings.max_retries,
            retry_wait=download_settings.retry_wait,
            verify_ssl=not self.config.settings.ignore_ssl_errors,
        )

        # 唯一解析器：消费 helper API 的统一响应
        self.parser = ApiParser()

        # 初始化下载器（仅在 helper 未提供 hashes 时回退使用）
        self.downloader = Downloader(
            max_retries=download_settings.max_retries,
            retry_wait=download_settings.retry_wait,
            timeout=download_settings.timeout,
            connections=download_settings.connections,
            show_progress=download_settings.show_progress,
            check_certificate=not self.config.settings.ignore_ssl_errors,
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

    def _build_fetch_url(self, package_name: str, hash_algorithm: str) -> str:
        """拼接 helper API 查询 URL：{base_url}/{name}?algorithm={algo}"""
        base_url = self.config.settings.api.base_url.rstrip("/")
        return f"{base_url}/{package_name}?algorithm={hash_algorithm}"

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

    def _check_pkgbuild_exists(self, package_config: PackageConfig) -> bool:
        """
        检查 PKGBUILD 文件是否存在

        Args:
            package_config: 包配置

        Returns:
            True 如果文件存在，False 否则
        """
        pkgbuild_path = self._get_pkgbuild_path(package_config.pkgbuild)
        if not pkgbuild_path.exists():
            logger.warning("  跳过: PKGBUILD 文件不存在: %s", pkgbuild_path)
            return False
        return True

    def _select_api_hashes(
        self, parsed: ParsedPackage, supported_archs: list[ArchEnum]
    ) -> dict[str, str]:
        """从 ``parsed.hashes`` 中挑选出支持架构的校验和。

        返回 ``{arch_value: checksum}``；缺失架构不计入（可能由调用方回退下载）。
        """
        checksums: dict[str, str] = {}
        for arch in supported_archs:
            checksum = parsed.hashes.get(arch.value)
            if checksum:
                checksums[arch.value] = checksum
            else:
                logger.warning("  API 未提供 %s 架构的 hash", arch.value)
        return checksums

    async def _get_checksums(
        self,
        parsed: ParsedPackage,
        supported_archs: list[ArchEnum],
        package_name: str,
        new_version: str,
        hash_algorithm: str,
        verify_only: bool = False,
    ) -> tuple[dict[str, str], bool]:
        """获取各架构校验和：优先用 helper API 提供的 hashes，否则下载计算。

        helper 通过 ``data.hashes`` 提供校验和时直接采用，跳过本地下载。若 hashes
        为空或缺部分架构，按 ``parsed.urls`` 下载缺失架构并在本地计算 hash。

        返回 ``(checksums, success)``。``success=False`` 仅在下载路径下有架构失败
        时出现（``verify_only=False``）；``verify_only=True`` 时即便全部失败也返回
        ``success=True``，但 ``checksums`` 为空，调用方需自行检查空字典。
        """
        api_hashes = self._select_api_hashes(parsed, supported_archs)
        if api_hashes and len(api_hashes) == len(supported_archs):
            logger.info("  使用 API 提供的校验和，跳过下载")
            return api_hashes, True

        # 部分/全部缺失 → 回退下载缺失架构
        missing_archs = [
            arch for arch in supported_archs if arch.value not in api_hashes
        ]
        arch_urls = {
            arch.value: parsed.urls[arch.value]
            for arch in missing_archs
            if arch.value in parsed.urls
        }
        if not arch_urls:
            logger.error(
                "  错误: 无法获取缺失架构的下载URL（API hashes 与 urls 均不足）"
            )
            return api_hashes, False

        logger.info("  API hashes 不完整，回退下载计算: %s", list(arch_urls))
        downloaded, success = await self._download_and_verify(
            package_name,
            new_version,
            arch_urls,
            hash_algorithm,
            verify_only=verify_only,
        )
        if not success:
            return api_hashes, False

        # 合并 API 提供的 + 本地计算的
        merged = {**api_hashes, **downloaded}
        return merged, True

    async def _download_and_verify(
        self,
        package_name: str,
        new_version: str,
        arch_urls: dict[str, str],
        hash_algorithm: str = HashAlgorithmEnum.B2.value,
        verify_only: bool = False,
    ) -> tuple[dict[str, str], bool]:
        """
        下载文件并计算校验和（回退路径）

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
            # 获取生效的哈希算法（包级覆盖 > 全局默认），同时决定 API 查询参数
            hash_algorithm = package_config.get_effective_hash_algorithm(
                self.config.settings.hash_algorithm
            )

            # 1. 从 helper API 获取最新版本信息
            fetch_url = self._build_fetch_url(package_config.name, hash_algorithm)
            logger.info("  1. 从 %s 获取版本信息...", fetch_url)
            response_data = await self.fetcher.fetch_text(fetch_url)
            if not response_data:
                logger.error("  错误: 无法获取版本信息")
                return False

            # 2. 解析统一响应
            logger.info("  2. 解析版本信息...")
            parsed = self.parser.parse(response_data)
            if parsed is None:
                logger.error("  错误: 无法解析版本信息")
                return False

            new_version = parsed.version
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

            # 版本比较
            version_comparison = compare_versions(new_version, current_version)

            if version_comparison <= 0:
                # 当前版本 >= 新版本，仅验证哈希
                return await self._handle_version_not_newer(
                    package_name,
                    new_version,
                    current_version,
                    version_comparison,
                    editor,
                    parsed,
                    supported_archs,
                    hash_algorithm,
                )

            # 版本更新流程
            return await self._handle_version_update(
                package_name,
                new_version,
                editor,
                parsed,
                supported_archs,
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
        editor: PKGBUILDEditor,
        parsed: ParsedPackage,
        supported_archs: list[ArchEnum],
        hash_algorithm: str = HashAlgorithmEnum.B2.value,
    ) -> bool:
        """
        处理版本不更新的情况（当前版本 >= 新版本）

        复用 update_package 已创建的 editor，避免重复加载 PKGBUILD。
        两种场景：
        1. 当前版本 > 新版本（version_comparison < 0）：版本降级，下载并验证
           远端哈希，不写 PKGBUILD。返回 True 仅在验证成功时。
        2. 当前版本 = 新版本（version_comparison == 0）：比较本地/远端哈希，
           若发生变化则自增 pkgrel 并写入新校验和，PKGBUILD 仍会被更新。

        Args:
            editor: update_package 已创建好的 PKGBUILDEditor，函数结束时不会
                自动 save——只在哈希发生变化时由本方法显式 save。
        """
        if version_comparison < 0:
            # 当前版本 > 新版本：版本降级
            logger.info(
                "  跳过更新: 新版本 %s 低于当前版本 %s", new_version, current_version
            )
            logger.info("  说明: 当前包版本较新，无需降级")
            logger.info("  注意: 仍将校验远端 hashes（API 提供）或下载验证...")

            # verify_only=True 时即便全部失败也返回 True，需自行校验空 checksums
            checksums, _ = await self._get_checksums(
                parsed,
                supported_archs,
                package_name,
                new_version,
                hash_algorithm,
                verify_only=True,
            )
            if not checksums:
                logger.error("  错误: 降级校验失败，所有架构均未拿到校验和")
                return False

            logger.info("  包 %s 验证完成（未更新 PKGBUILD）", package_name)
            return True

        # 当前版本 = 新版本：检查哈希变化
        logger.info("  版本未变化，检查文件哈希是否变化...")

        # 复用 update_package 传入的 editor，直接读取当前 PKGBUILD 的哈希
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

        # 获取远端 hashes：API 优先提供，否则下载计算
        new_checksums, success = await self._get_checksums(
            parsed,
            supported_archs,
            package_name,
            new_version,
            hash_algorithm,
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
        editor: PKGBUILDEditor,
        parsed: ParsedPackage,
        supported_archs: list[ArchEnum],
        package_config: PackageConfig,
        hash_algorithm: str = HashAlgorithmEnum.B2.value,
    ) -> bool:
        """
        处理版本更新流程（new_version > current_version）。

        步骤：
        1. 获取 checksums：API 优先提供，否则按 urls 下载计算
        2. 若 update_source_url=True，用 parsed.urls 写入 PKGBUILD source 字段
        3. 更新 PKGBUILD：pkgver、pkgrel=1、source、checksum
        4. save 写入磁盘
        """
        logger.info("  3. 获取校验和（API 提供 or 下载）...")
        logger.info("  支持的架构: %s", [arch.value for arch in supported_archs])

        # 获取 checksums：API 优先，否则 fallback 到下载
        checksums, success = await self._get_checksums(
            parsed,
            supported_archs,
            package_name,
            new_version,
            hash_algorithm,
        )
        if not success:
            return False

        # 更新 PKGBUILD
        logger.info("  4. 更新 PKGBUILD 版本和校验和...")
        editor.update_pkgver(new_version)
        editor.update_pkgrel(1)  # 重置 pkgrel 为 1

        # 更新 source 和校验和；ANY 架构用非架构特定字段，其余用架构特定字段
        for arch_value, checksum in checksums.items():
            field_arch = None if arch_value == ArchEnum.ANY.value else arch_value
            if package_config.update_source_url:
                source_url = parsed.urls.get(arch_value)
                if source_url:
                    editor.update_source(source_url, arch=field_arch)
                else:
                    logger.warning("  API urls 中无 %s 架构的 URL", arch_value)
            editor.update_checksum(checksum, hash_algorithm, arch=field_arch)

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
            if not self._check_pkgbuild_exists(package_config):
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

        if not self._check_pkgbuild_exists(package_config):
            return False, f"包 '{package_name}' PKGBUILD 文件不存在"

        return True, None

    async def _run_updates(
        self, valid_packages: dict[str, PackageConfig]
    ) -> tuple[int, int]:
        """并行更新 valid_packages 中的包，返回 (成功数, 总数)"""
        tasks = [
            self.update_package(name, config) for name, config in valid_packages.items()
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
