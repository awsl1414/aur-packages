import re
from pathlib import Path
from typing import Union

from constants import HashAlgorithmEnum
from utils.hash import (
    calculate_file_hash,
    calculate_sha256,
    calculate_multiple_hashes,
    verify_file_hash,
    download_and_verify,
    format_checksum_for_pkgbuild,
    format_multiple_checksums_for_pkgbuild,
)


class PKGBUILDEditor:
    """
    PKGBUILD文件编辑器，用于更新版本、校验和等信息
    """

    def __init__(self, pkgbuild_path: Path):
        """
        初始化PKGBUILD编辑器

        Args:
            pkgbuild_path: PKGBUILD文件路径
        """
        self.pkgbuild_path = pkgbuild_path
        self.content = ""
        self._load_content()

    def _load_content(self) -> None:
        """加载PKGBUILD文件内容"""
        with open(self.pkgbuild_path, "r", encoding="utf-8") as f:
            self.content = f.read()

    def _save_content(self) -> None:
        """保存PKGBUILD文件内容"""
        with open(self.pkgbuild_path, "w", encoding="utf-8") as f:
            f.write(self.content)

    def update_pkgver(self, new_version: str) -> None:
        """
        更新pkgver字段

        Args:
            new_version: 新版本号
        """
        pattern = r"^pkgver=.*$"
        replacement = f"pkgver={new_version}"
        self.content = re.sub(pattern, replacement, self.content, flags=re.MULTILINE)

    def update_pkgrel(self, new_pkgrel: int = 1) -> None:
        """
        更新pkgrel字段

        Args:
            new_pkgrel: 新的发布号，默认为1
        """
        pattern = r"^pkgrel=.*$"
        replacement = f"pkgrel={new_pkgrel}"
        self.content = re.sub(pattern, replacement, self.content, flags=re.MULTILINE)

    def update_epoch(self, new_epoch: int | None = None) -> None:
        """
        更新epoch字段

        Args:
            new_epoch: 新的epoch值，如果为None则不更新
        """
        if new_epoch is None:
            return

        # 检查epoch字段是否存在
        if re.search(r"^epoch=.*$", self.content, flags=re.MULTILINE):
            pattern = r"^epoch=.*$"
            replacement = f"epoch={new_epoch}"
            self.content = re.sub(
                pattern, replacement, self.content, flags=re.MULTILINE
            )
        else:
            # 如果不存在，在pkgver之前添加
            pattern = r"^(pkgver=.*)$"
            replacement = f"epoch={new_epoch}\n\1"
            self.content = re.sub(
                pattern, replacement, self.content, flags=re.MULTILINE
            )

    def update_sha512sums(self, new_checksum: str) -> None:
        """
        更新通用sha512sums字段

        Args:
            new_checksum: 新的SHA512校验和
        """
        pattern = r"^sha512sums=\(.*\)$"
        replacement = f"sha512sums=('{new_checksum}')"
        self.content = re.sub(pattern, replacement, self.content, flags=re.MULTILINE)

    def update_arch_checksum(self, arch: str, new_checksum: str) -> None:
        """
        更新特定架构的sha512sums字段

        Args:
            arch: 架构名称，如'x86_64', 'aarch64', 'loong64'
            new_checksum: 新的SHA512校验和
        """
        pattern = f"^sha512sums_{arch}=\\(.*\\)$"
        replacement = f"sha512sums_{arch}=('{new_checksum}')"
        self.content = re.sub(pattern, replacement, self.content, flags=re.MULTILINE)

    def update_source_url(self, arch: str, new_url: str) -> None:
        """
        更新特定架构的source URL

        Args:
            arch: 架构名称，如'x86_64', 'aarch64', 'loong64'
            new_url: 新的源码URL
        """
        pattern = f"^source_{arch}=\\(.*\\)$"
        replacement = f"source_{arch}=('{new_url}')"
        self.content = re.sub(pattern, replacement, self.content, flags=re.MULTILINE)

    def get_pkgver(self) -> str:
        """
        获取当前pkgver值

        Returns:
            当前的pkgver值
        """
        match = re.search(r"^pkgver=(.*)$", self.content, flags=re.MULTILINE)
        return match.group(1) if match else ""

    def get_pkgrel(self) -> int:
        """
        获取当前pkgrel值

        Returns:
            当前的pkgrel值
        """
        match = re.search(r"^pkgrel=(.*)$", self.content, flags=re.MULTILINE)
        return int(match.group(1)) if match else 1

    def get_epoch(self) -> int | None:
        """
        获取当前epoch值

        Returns:
            当前的epoch值，如果不存在则返回None
        """
        match = re.search(r"^epoch=(.*)$", self.content, flags=re.MULTILINE)
        return int(match.group(1)) if match else None

    def get_checksum(self, arch: str | None = None) -> str:
        """
        获取当前sha512sums值

        Args:
            arch: 架构名称，如果为None则获取通用sha512sums

        Returns:
            当前的sha512sums值
        """
        if arch:
            pattern = f"^sha512sums_{arch}=\\('(.*)'\\)$"
        else:
            pattern = r"^sha512sums=\(\'(.*)\'\)$"

        match = re.search(pattern, self.content, flags=re.MULTILINE)
        return match.group(1) if match else ""

    def update_all(
        self,
        new_version: str,
        new_checksums: dict[str, str],
        new_urls: dict[str, str],
        new_pkgrel: int = 1,
        new_epoch: int | None = None,
        generic_checksum: str | None = None,
    ) -> None:
        """
        一次性更新所有相关字段

        Args:
            new_version: 新版本号
            new_checksums: 各架构的SHA512校验和，键为架构名，值为校验和
            new_urls: 各架构的源码URL，键为架构名，值为URL
            new_pkgrel: 新的发布号，默认为1
            new_epoch: 新的epoch值，如果为None则不更新
            generic_checksum: 通用的SHA512校验和，如果为None则不更新
        """
        # 更新版本和发布号
        self.update_pkgver(new_version)
        self.update_pkgrel(new_pkgrel)

        # 更新epoch（如果提供）
        if new_epoch:
            self.update_epoch(new_epoch)

        # 更新通用校验和（如果提供）
        if generic_checksum:
            self.update_sha512sums(generic_checksum)

        # 更新各架构的校验和和URL
        for arch, checksum in new_checksums.items():
            self.update_arch_checksum(arch, checksum)

        for arch, url in new_urls.items():
            self.update_source_url(arch, url)

    def save(self) -> None:
        """保存所有更改到PKGBUILD文件"""
        self._save_content()

    def reload(self) -> None:
        """重新加载PKGBUILD文件内容，放弃所有未保存的更改"""
        self._load_content()

    def calculate_and_update_checksum(
        self,
        file_path: Union[str, Path],
        arch: str | None = None,
        hash_algorithm: str = HashAlgorithmEnum.SHA512.value,
    ) -> None:
        """
        计算文件的校验和并更新到PKGBUILD

        Args:
            file_path: 要计算校验和的文件路径
            arch: 架构名称，如果为None则更新通用sha512sums
            hash_algorithm: 哈希算法，支持 'md5', 'sha1', 'sha256', 'sha512' 等
        """
        checksum = calculate_file_hash(file_path, hash_algorithm)

        if arch:
            if hash_algorithm == HashAlgorithmEnum.SHA512.value:
                self.update_arch_checksum(arch, checksum)
            else:
                # 对于其他哈希算法，使用通用更新方法
                pattern = f"^{hash_algorithm}sums_{arch}=\\(.*\\)$"
                replacement = f"{hash_algorithm}sums_{arch}=('{checksum}')"
                self.content = re.sub(
                    pattern, replacement, self.content, flags=re.MULTILINE
                )
        else:
            if hash_algorithm == HashAlgorithmEnum.SHA512.value:
                self.update_sha512sums(checksum)
            else:
                # 对于其他哈希算法，使用通用更新方法
                pattern = f"^{hash_algorithm}sums=\\(.*\\)$"
                replacement = f"{hash_algorithm}sums=('{checksum}')"
                self.content = re.sub(
                    pattern, replacement, self.content, flags=re.MULTILINE
                )

    def calculate_and_update_sha256(
        self, file_path: Union[str, Path], arch: str | None = None
    ) -> None:
        """
        计算文件的SHA256校验和并更新到PKGBUILD

        Args:
            file_path: 要计算校验和的文件路径
            arch: 架构名称，如果为None则更新通用sha256sums
        """
        self.calculate_and_update_checksum(
            file_path, arch, HashAlgorithmEnum.SHA256.value
        )

    def calculate_and_update_all_checksums(
        self,
        file_paths: dict[str, Union[str, Path]],
        generic_file: Union[str, Path] | None = None,
        hash_algorithm: str = HashAlgorithmEnum.SHA512.value,
    ) -> None:
        """
        计算多个文件的校验和并更新到PKGBUILD

        Args:
            file_paths: 各架构的文件路径，键为架构名，值为文件路径
            generic_file: 通用文件路径
            hash_algorithm: 哈希算法，支持 'md5', 'sha1', 'sha256', 'sha512' 等
        """
        # 更新各架构的校验和
        for arch, file_path in file_paths.items():
            self.calculate_and_update_checksum(file_path, arch, hash_algorithm)

        # 更新通用校验和
        if generic_file:
            self.calculate_and_update_checksum(generic_file, None, hash_algorithm)

    def download_and_verify_checksum(
        self,
        url: str,
        destination: Union[str, Path],
        expected_hash: str,
        arch: str | None = None,
        hash_algorithm: str = HashAlgorithmEnum.SHA512.value,
    ) -> bool:
        """
        下载文件并验证其哈希值，如果验证成功则更新到PKGBUILD

        Args:
            url: 下载URL
            destination: 保存路径
            expected_hash: 预期的哈希值
            arch: 架构名称，如果为None则更新通用校验和
            hash_algorithm: 哈希算法，默认为 'sha512'

        Returns:
            如果下载成功且哈希值匹配返回True，否则返回False
        """
        if download_and_verify(url, destination, expected_hash, hash_algorithm):
            self.calculate_and_update_checksum(destination, arch, hash_algorithm)
            return True
        return False

    def verify_existing_checksum(
        self,
        file_path: Union[str, Path],
        expected_hash: str,
        arch: str | None = None,
        hash_algorithm: str = HashAlgorithmEnum.SHA512.value,
    ) -> bool:
        """
        验证现有文件的哈希值是否匹配预期值

        Args:
            file_path: 文件路径
            expected_hash: 预期的哈希值
            arch: 架构名称，如果为None则验证通用校验和
            hash_algorithm: 哈希算法，默认为 'sha512'

        Returns:
            如果哈希值匹配返回True，否则返回False
        """
        return verify_file_hash(file_path, expected_hash, hash_algorithm)

    def get_formatted_checksums(self) -> dict[str, str]:
        """
        获取当前PKGBUILD中所有格式化的校验和

        Returns:
            包含所有校验和的字典，键为校验和字段名，值为格式化的校验和字符串
        """
        result = {}

        # 获取通用校验和
        for algo in HashAlgorithmEnum.get_all():
            pattern = f"^{algo}sums=\\('(.*)'\\)$"
            match = re.search(pattern, self.content, flags=re.MULTILINE)
            if match:
                result[f"{algo}sums"] = match.group(0)

        # 获取各架构的校验和
        for algo in HashAlgorithmEnum.get_all():
            for arch in ["x86_64", "aarch64", "loong64", "i686", "armv7h"]:
                pattern = f"^{algo}sums_{arch}=\\('(.*)'\\)$"
                match = re.search(pattern, self.content, flags=re.MULTILINE)
                if match:
                    result[f"{algo}sums_{arch}"] = match.group(0)

        return result

    def get_file_checksums(self, file_path: Union[str, Path]) -> dict[str, str]:
        """
        获取文件的所有格式化校验和

        Args:
            file_path: 要计算校验和的文件路径

        Returns:
            包含所有格式化校验和的字典
        """
        file_path = Path(file_path)
        checksums = {}

        # 计算所有支持的哈希值
        for algorithm in HashAlgorithmEnum.get_all():
            hash_value = calculate_file_hash(file_path, algorithm)
            checksums[algorithm] = format_checksum_for_pkgbuild(hash_value)

        return checksums

    def get_all_checksums(self, file_path: Union[str, Path]) -> dict[str, str]:
        """
        获取文件的所有校验和（原始值）

        Args:
            file_path: 要计算校验和的文件路径

        Returns:
            包含所有校验和的字典
        """
        return calculate_multiple_hashes(file_path, HashAlgorithmEnum.get_all())