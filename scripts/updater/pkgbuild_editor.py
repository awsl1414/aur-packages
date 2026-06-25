"""PKGBUILD 文件编辑器模块"""

import re
from pathlib import Path

from constants.constants import HashAlgorithmEnum

# shell 变量引用：匹配 ${VAR} 或 $VAR / $_VAR（无花括号形式）
_SHELL_VAR_RE = re.compile(r"\$\{|\$[A-Za-z_]")
# 远程 URL 协议头，如 https://、git+https://
_REMOTE_PROTO_RE = re.compile(r"^[a-z][a-z0-9+.\-]*://", re.IGNORECASE)
# source 数组内的引号条目（双引号或单引号）
_SOURCE_ENTRY_RE = re.compile(r'"([^"]*)"|\'([^\']*)\'')


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
        """更新特定架构的 source URL，保留别名与本地源条目；URL 含 shell 变量时跳过"""
        self._update_source_field(re.escape(f"source_{arch}"), new_url)

    def update_source(self, new_url: str) -> None:
        """更新非架构特定 source URL（用于 arch=('any') 包），保留别名与本地源条目；URL 含 shell 变量时跳过"""
        self._update_source_field(re.escape("source"), new_url)

    @staticmethod
    def _has_shell_var(text: str) -> bool:
        """文本是否包含 shell 变量引用（${VAR} 或 $VAR/$_VAR）"""
        return _SHELL_VAR_RE.search(text) is not None

    @staticmethod
    def _is_remote_entry(value: str) -> bool:
        """source 条目是否为远程 URL（带 :: 别名或以协议头开头）"""
        return "::" in value or bool(_REMOTE_PROTO_RE.match(value))

    def _update_source_field(self, field_pattern: str, new_url: str) -> None:
        """更新 source / source_<arch> 字段的远程 URL。

        - 支持单行/多行、单条目/多条目数组；本地源条目（如 launcher.sh）原样保留。
        - 仅替换第一个远程条目；其 URL 部分含 shell 变量引用时整段保留。
        - 别名中的 shell 变量（如 ${pkgver}，用于文件名缓存破除）始终保留。
        - re.sub 用函数返回替换文本，避免 new_url/alias 中的反斜杠被当作反向引用。
        """
        block_re = re.compile(
            rf"^({field_pattern})=\((.*?)\)\s*$",
            re.MULTILINE | re.DOTALL,
        )
        match = block_re.search(self.content)
        if not match:
            return  # 字段缺失，保持原样

        field = match.group(1)
        inner = match.group(2)
        entries = [
            em.group(1) if em.group(1) is not None else em.group(2)
            for em in _SOURCE_ENTRY_RE.finditer(inner)
        ]
        if not entries:
            return  # 空数组，保持原样

        remote_idx = next(
            (i for i, entry in enumerate(entries) if self._is_remote_entry(entry)),
            None,
        )
        if remote_idx is None:
            return  # 无远程条目，保持原样

        target = entries[remote_idx]
        if "::" in target:
            # 首个 :: 分隔别名与 URL，与 makepkg 语义一致
            alias, _, url = target.partition("::")
            if self._has_shell_var(url):
                return  # URL 含 shell 变量引用，保留模板
            entries[remote_idx] = f"{alias}::{new_url}"
        else:
            if self._has_shell_var(target):
                return
            entries[remote_idx] = new_url

        new_inner = " ".join(f'"{entry}"' for entry in entries)
        new_block = f"{field}=({new_inner})"
        # count=1：仅更新第一个匹配块；lambda 返回值不被解析为反向引用模板
        self.content = block_re.sub(
            lambda _m: new_block, self.content, count=1
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
