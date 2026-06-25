"""PKGBUILD 文件编辑器模块"""

import re
from pathlib import Path

from constants.constants import HashAlgorithmEnum


class PKGBUILDEditor:
    """PKGBUILD 文件编辑器，支持上下文管理器自动保存"""

    def __init__(self, pkgbuild_path: Path) -> None:
        self.pkgbuild_path = pkgbuild_path
        self.content = ""
        self._load_content()

    def __enter__(self) -> "PKGBUILDEditor":
        return self

    def __exit__(
        self, exc_type: type | None, exc_val: BaseException | None, exc_tb: object
    ) -> None:
        if exc_type is None:
            self.save()

    def _load_content(self) -> None:
        """加载 PKGBUILD 文件内容"""
        with open(self.pkgbuild_path, "r", encoding="utf-8") as f:
            self.content = f.read()

    def _save_content(self) -> None:
        """保存 PKGBUILD 文件内容"""
        with open(self.pkgbuild_path, "w", encoding="utf-8") as f:
            f.write(self.content)

    def update_pkgver(self, new_version: str) -> None:
        """更新 pkgver 字段"""
        pattern = r"^pkgver=.*$"
        replacement = f"pkgver={new_version}"
        self.content = re.sub(pattern, replacement, self.content, flags=re.MULTILINE)

    def update_pkgrel(self, new_pkgrel: int = 1) -> None:
        """更新 pkgrel 字段"""
        pattern = r"^pkgrel=.*$"
        replacement = f"pkgrel={new_pkgrel}"
        self.content = re.sub(pattern, replacement, self.content, flags=re.MULTILINE)

    def update_epoch(self, new_epoch: int | None = None) -> None:
        """更新或添加 epoch 字段"""
        if new_epoch is None:
            return

        if re.search(r"^epoch=.*$", self.content, flags=re.MULTILINE):
            pattern = r"^epoch=.*$"
            replacement = f"epoch={new_epoch}"
            self.content = re.sub(
                pattern, replacement, self.content, flags=re.MULTILINE
            )
        else:
            pattern = r"^(pkgver=.*)$"
            replacement = f"epoch={new_epoch}\n\1"
            self.content = re.sub(
                pattern, replacement, self.content, flags=re.MULTILINE
            )

    def update_arch_checksum(
        self,
        arch: str,
        new_checksum: str,
        hash_algorithm: str = HashAlgorithmEnum.SHA512.value,
    ) -> None:
        """更新特定架构的校验和字段"""
        pattern = f"^{hash_algorithm}sums_{arch}=\\(.*\\)$"
        replacement = f"{hash_algorithm}sums_{arch}=('{new_checksum}')"
        self.content = re.sub(pattern, replacement, self.content, flags=re.MULTILINE)

    def update_source_url(self, arch: str, new_url: str) -> None:
        """更新特定架构的 source URL，保留已有的 :: 别名"""
        escaped_arch = re.escape(arch)
        # Capture both alias (group 1) and existing URL (group 2)
        pattern = f"^source_{escaped_arch}=\\(['\"]([^'\"]*?)::([^'\"]*?)['\"]\\)$"
        match = re.search(pattern, self.content, flags=re.MULTILINE)

        if match:
            alias = match.group(1)
            existing_url = match.group(2)
            # Preserve shell variable references (e.g. ${_gh}/...)
            if "${" in existing_url:
                return
            replacement = f'source_{arch}=("{alias}::{new_url}")'
        else:
            replacement = f"source_{arch}=('{new_url}')"

        self.content = re.sub(
            f"^source_{escaped_arch}=\\(.*\\)$",
            replacement,
            self.content,
            flags=re.MULTILINE,
        )

    def update_source(self, new_url: str) -> None:
        """更新非架构特定的 source URL（用于 arch=('any') 包），保留已有的 :: 别名"""
        # 匹配单引号或双引号包裹的 :: 别名格式
        pattern = r"""^source=\((?:['"]([^'"]*)::[^'"]*['"]|.*)\)$"""
        match = re.search(pattern, self.content, flags=re.MULTILINE)
        if match and match.group(1):
            replacement = f'source=("{match.group(1)}::{new_url}")'
        else:
            replacement = f"source=('{new_url}')"
        self.content = re.sub(
            r"^source=\(.*\)$",
            replacement,
            self.content,
            flags=re.MULTILINE,
        )

    def update_checksum(
        self,
        new_checksum: str,
        hash_algorithm: str = HashAlgorithmEnum.SHA512.value,
    ) -> None:
        """更新非架构特定的校验和字段（用于 arch=('any') 包）"""
        pattern = f"^{hash_algorithm}sums=\\(.*\\)$"
        replacement = f"{hash_algorithm}sums=('{new_checksum}')"
        self.content = re.sub(pattern, replacement, self.content, flags=re.MULTILINE)

    def get_pkgver(self) -> str:
        """获取当前 pkgver 值"""
        match = re.search(r"^pkgver=(.*)$", self.content, flags=re.MULTILINE)
        return match.group(1) if match else ""

    def get_pkgrel(self) -> int:
        """获取当前 pkgrel 值"""
        match = re.search(r"^pkgrel=(.*)$", self.content, flags=re.MULTILINE)
        if not match:
            return 1
        try:
            return int(match.group(1))
        except ValueError:
            return 1

    def get_epoch(self) -> int | None:
        """获取当前 epoch 值"""
        match = re.search(r"^epoch=(.*)$", self.content, flags=re.MULTILINE)
        if not match:
            return None
        try:
            return int(match.group(1))
        except ValueError:
            return None

    def get_checksum(
        self,
        arch: str | None = None,
        hash_algorithm: str = HashAlgorithmEnum.SHA512.value,
    ) -> str:
        """获取当前校验和值"""
        if arch:
            pattern = f"^{hash_algorithm}sums_{arch}=\\((?:'([^']*)'.*)?\\)$"
        else:
            pattern = f"^{hash_algorithm}sums=\\((?:'([^']*)'.*)?\\)$"

        match = re.search(pattern, self.content, flags=re.MULTILINE)
        return match.group(1) if match else ""

    def save(self) -> None:
        """保存所有更改到文件"""
        self._save_content()

    def reload(self) -> None:
        """重新加载文件内容，放弃未保存的更改"""
        self._load_content()
