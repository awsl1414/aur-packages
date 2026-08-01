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

    def _update_scalar_field(self, field: str, value: str) -> None:
        """替换 ^field=.*$ 整行为 field=value（MULTILINE）。字段不存在时无操作。

        用 lambda 返回替换文本，避免 value 中的反斜杠被当作反向引用（与
        _update_source_field 的安全姿态一致）。
        """
        self.content = re.sub(
            rf"^{re.escape(field)}=.*$",
            lambda _m: f"{field}={value}",
            self.content,
            flags=re.MULTILINE,
        )

    def _get_scalar_field(self, field: str) -> str | None:
        """返回 ^field=(.*)$ 的捕获值；字段不存在返回 None。"""
        match = re.search(
            rf"^{re.escape(field)}=(.*)$", self.content, flags=re.MULTILINE
        )
        return match.group(1) if match else None

    def _get_scalar_field_as_int(self, field: str, default: int | None) -> int | None:
        """取标量并按 int 解析；缺失或解析失败返回 default。"""
        raw = self._get_scalar_field(field)
        if raw is None:
            return default
        try:
            return int(raw)
        except ValueError:
            return default

    def update_pkgver(self, new_version: str) -> None:
        """更新 pkgver 字段"""
        self._update_scalar_field("pkgver", new_version)

    def update_pkgrel(self, new_pkgrel: int = 1) -> None:
        """更新 pkgrel 字段"""
        self._update_scalar_field("pkgrel", str(new_pkgrel))

    def update_epoch(self, new_epoch: int | None = None) -> None:
        """更新或添加 epoch 字段"""
        if new_epoch is None:
            return
        if self._get_scalar_field("epoch") is not None:
            self._update_scalar_field("epoch", str(new_epoch))
        else:
            # pkgver 之前插入 epoch 行
            self.content = re.sub(
                r"^(pkgver=.*)$",
                f"epoch={new_epoch}\n\\1",
                self.content,
                flags=re.MULTILINE,
            )

    def update_source(self, new_url: str, *, arch: str | None = None) -> None:
        """更新 source URL，保留别名与本地源条目；URL 含 shell 变量时跳过。

        arch=None 更新非架构特定 source=()（arch=('any') 包），否则更新 source_<arch>=()。
        """
        field = "source" if arch is None else f"source_{arch}"
        self._update_source_field(re.escape(field), new_url)

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
        self.content = block_re.sub(lambda _m: new_block, self.content, count=1)

    def update_checksum(
        self,
        new_checksum: str,
        hash_algorithm: str = HashAlgorithmEnum.B2.value,
        *,
        arch: str | None = None,
    ) -> None:
        """更新校验和字段。

        arch=None 更新非架构特定 sums=()（arch=('any') 包），否则更新 sums_<arch>=()。
        """
        field = (
            f"{hash_algorithm}sums_{arch}"
            if arch is not None
            else f"{hash_algorithm}sums"
        )
        self._update_scalar_field(field, f"('{new_checksum}')")

    def get_pkgver(self) -> str:
        """获取当前 pkgver 值"""
        return self._get_scalar_field("pkgver") or ""

    def get_pkgrel(self) -> int:
        """获取当前 pkgrel 值"""
        value = self._get_scalar_field_as_int("pkgrel", 1)
        return value if value is not None else 1

    def get_epoch(self) -> int | None:
        """获取当前 epoch 值"""
        return self._get_scalar_field_as_int("epoch", None)

    def get_checksum(
        self,
        *,
        arch: str | None = None,
        hash_algorithm: str = HashAlgorithmEnum.B2.value,
    ) -> str:
        """获取当前校验和值。

        arch=None 读取非架构特定 sums=()（arch=('any') 包），否则读取 sums_<arch>=()。
        """
        if arch:
            pattern = f"^{hash_algorithm}sums_{arch}=\\((?:'([^']*)'.*)?\\)$"
        else:
            pattern = f"^{hash_algorithm}sums=\\((?:'([^']*)'.*)?\\)$"

        match = re.search(pattern, self.content, flags=re.MULTILINE)
        return match.group(1) if match else ""

    def save(self) -> None:
        """保存所有更改到文件"""
        self._save_content()
