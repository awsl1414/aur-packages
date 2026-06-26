"""PKGBUILD 编辑器单元测试"""

from pathlib import Path

import pytest

from constants.constants import HashAlgorithmEnum
from updater.pkgbuild_editor import PKGBUILDEditor

PKGBUILD_TEMPLATE: str = """\
# Maintainer: test <test@test.com>
pkgname=test-pkg
pkgver=1.0.0
pkgrel=1
arch=('x86_64' 'aarch64')
source=("test.sh" "test.desktop")
source_x86_64=('https://example.com/test-1.0.0-x86_64.tar.gz')
source_aarch64=('https://example.com/test-1.0.0-aarch64.tar.gz')
sha512sums=('SKIP' 'SKIP')
sha512sums_x86_64=('aaa111')
sha512sums_aarch64=('bbb222')
"""

PKGBUILD_B2: str = """\
# Maintainer: test <test@test.com>
pkgname=test-pkg
pkgver=1.0.0
pkgrel=1
arch=('x86_64' 'aarch64')
source=("test.sh" "test.desktop")
source_x86_64=('https://example.com/test-1.0.0-x86_64.tar.gz')
source_aarch64=('https://example.com/test-1.0.0-aarch64.tar.gz')
b2sums=('c1c1c1' 'd2d2d2')
b2sums_x86_64=('eee333')
b2sums_aarch64=('fff444')
"""

PKGBUILD_WITH_EPOCH: str = """\
# Maintainer: test <test@test.com>
pkgname=test-pkg
epoch=5
pkgver=1.0.0
pkgrel=1
sha512sums_x86_64=('aaa111')
"""

PKGBUILD_ALIAS: str = """\
# Maintainer: test <test@test.com>
pkgname=test-pkg
pkgver=1.0.0
pkgrel=1
source_x86_64=("test-${pkgver}-${pkgrel}.tar.gz::https://example.com/test.tar.gz")
sha512sums_x86_64=('aaa111')
"""


@pytest.fixture
def pkgbuild(tmp_path) -> Path:
    """创建临时 PKGBUILD 文件"""
    p = tmp_path / "PKGBUILD"
    p.write_text(PKGBUILD_TEMPLATE, encoding="utf-8")
    return p


class TestPKGBUILDEditorGetters:
    def test_get_pkgver(self, pkgbuild) -> None:
        editor = PKGBUILDEditor(pkgbuild)
        assert editor.get_pkgver() == "1.0.0"

    def test_get_pkgrel(self, pkgbuild) -> None:
        editor = PKGBUILDEditor(pkgbuild)
        assert editor.get_pkgrel() == 1

    def test_get_checksum(self, pkgbuild) -> None:
        editor = PKGBUILDEditor(pkgbuild)
        sha512 = HashAlgorithmEnum.SHA512.value
        assert editor.get_checksum(arch="x86_64", hash_algorithm=sha512) == "aaa111"
        assert editor.get_checksum(arch="aarch64", hash_algorithm=sha512) == "bbb222"

    def test_get_checksum_no_arch(self, pkgbuild) -> None:
        editor = PKGBUILDEditor(pkgbuild)
        assert editor.get_checksum(hash_algorithm=HashAlgorithmEnum.SHA512.value) == "SKIP"

    def test_get_checksum_b2(self, tmp_path: Path) -> None:
        """获取 b2sums 校验和"""
        p = tmp_path / "PKGBUILD"
        p.write_text(PKGBUILD_B2, encoding="utf-8")
        editor = PKGBUILDEditor(p)
        b2 = HashAlgorithmEnum.B2.value
        assert editor.get_checksum(arch="x86_64", hash_algorithm=b2) == "eee333"
        assert editor.get_checksum(arch="aarch64", hash_algorithm=b2) == "fff444"

    def test_get_checksum_b2_no_arch(self, tmp_path: Path) -> None:
        """获取 b2sums 无架构校验和"""
        p = tmp_path / "PKGBUILD"
        p.write_text(PKGBUILD_B2, encoding="utf-8")
        editor = PKGBUILDEditor(p)
        assert (
            editor.get_checksum(hash_algorithm=HashAlgorithmEnum.B2.value) == "c1c1c1"
        )

    def test_get_checksum_algorithm_not_found(self, pkgbuild) -> None:
        """PKGBUILD 中不存在该算法的校验和时返回空字符串"""
        editor = PKGBUILDEditor(pkgbuild)
        assert editor.get_checksum(arch="x86_64", hash_algorithm=HashAlgorithmEnum.B2.value) == ""


class TestPKGBUILDEditorUpdate:
    def test_update_pkgver(self, pkgbuild) -> None:
        editor = PKGBUILDEditor(pkgbuild)
        editor.update_pkgver("2.0.0")
        assert editor.get_pkgver() == "2.0.0"

    def test_update_pkgrel(self, pkgbuild) -> None:
        editor = PKGBUILDEditor(pkgbuild)
        editor.update_pkgrel(3)
        assert editor.get_pkgrel() == 3

    def test_update_checksum_arch(self, pkgbuild) -> None:
        editor = PKGBUILDEditor(pkgbuild)
        sha512 = HashAlgorithmEnum.SHA512.value
        editor.update_checksum("newhash123", sha512, arch="x86_64")
        assert editor.get_checksum(arch="x86_64", hash_algorithm=sha512) == "newhash123"

    def test_update_checksum_arch_b2(self, tmp_path: Path) -> None:
        """更新 b2sums 架构校验和"""
        p = tmp_path / "PKGBUILD"
        p.write_text(PKGBUILD_B2, encoding="utf-8")
        editor = PKGBUILDEditor(p)
        b2 = HashAlgorithmEnum.B2.value
        editor.update_checksum("new_b2_hash", b2, arch="x86_64")
        assert editor.get_checksum(arch="x86_64", hash_algorithm=b2) == "new_b2_hash"

    def test_update_source_arch(self, pkgbuild) -> None:
        editor = PKGBUILDEditor(pkgbuild)
        editor.update_source("https://example.com/test-2.0.0-x86_64.tar.gz", arch="x86_64")
        assert "test-2.0.0-x86_64" in editor.content

    def test_save_and_reopen(self, pkgbuild) -> None:
        editor = PKGBUILDEditor(pkgbuild)
        editor.update_pkgver("3.0.0")
        editor.save()

        editor2 = PKGBUILDEditor(pkgbuild)
        assert editor2.get_pkgver() == "3.0.0"


class TestPKGBUILDEditorEpoch:
    """update_epoch 和 get_epoch 测试"""

    def test_update_epoch_existing(self, tmp_path: Path) -> None:
        """替换已有的 epoch 行"""
        p = tmp_path / "PKGBUILD"
        p.write_text(PKGBUILD_WITH_EPOCH, encoding="utf-8")
        editor = PKGBUILDEditor(p)
        editor.update_epoch(10)
        assert editor.get_epoch() == 10

    def test_update_epoch_insert(self, pkgbuild) -> None:
        """无 epoch 行时在 pkgver 前插入"""
        editor = PKGBUILDEditor(pkgbuild)
        assert editor.get_epoch() is None
        editor.update_epoch(5)
        assert editor.get_epoch() == 5

    def test_update_epoch_none(self, pkgbuild) -> None:
        """new_epoch=None 时不做任何修改"""
        editor = PKGBUILDEditor(pkgbuild)
        original = editor.content
        editor.update_epoch(None)
        assert editor.content == original

    def test_get_epoch_non_integer(self, tmp_path: Path) -> None:
        """epoch 值非整数时返回 None"""
        p = tmp_path / "PKGBUILD"
        p.write_text("pkgname=test\nepoch=abc\npkgver=1.0\n", encoding="utf-8")
        editor = PKGBUILDEditor(p)
        assert editor.get_epoch() is None


class TestPKGBUILDEditorEdgeCases:
    """边界条件测试"""

    def test_get_pkgrel_non_integer(self, tmp_path: Path) -> None:
        """pkgrel 非数字时返回默认值 1"""
        p = tmp_path / "PKGBUILD"
        p.write_text("pkgname=test\npkgver=1.0\npkgrel=abc\n", encoding="utf-8")
        editor = PKGBUILDEditor(p)
        assert editor.get_pkgrel() == 1

    def test_get_pkgrel_missing(self, tmp_path: Path) -> None:
        """无 pkgrel 行时返回默认值 1"""
        p = tmp_path / "PKGBUILD"
        p.write_text("pkgname=test\npkgver=1.0\n", encoding="utf-8")
        editor = PKGBUILDEditor(p)
        assert editor.get_pkgrel() == 1

    def test_source_url_alias_preserved(self, tmp_path: Path) -> None:
        """更新 source URL 时保留 :: 别名"""
        p = tmp_path / "PKGBUILD"
        p.write_text(PKGBUILD_ALIAS, encoding="utf-8")
        editor = PKGBUILDEditor(p)
        editor.update_source("https://example.com/test-v2.tar.gz", arch="x86_64")
        assert "test-${pkgver}-${pkgrel}.tar.gz::" in editor.content
        assert "test-v2.tar.gz" in editor.content


class TestPKGBUILDEditorContextManager:
    """上下文管理器测试"""

    def test_auto_save_on_normal_exit(self, pkgbuild) -> None:
        """with 块正常退出时自动保存"""
        with PKGBUILDEditor(pkgbuild) as editor:
            editor.update_pkgver("9.0.0")

        # 重新加载验证已保存
        editor2 = PKGBUILDEditor(pkgbuild)
        assert editor2.get_pkgver() == "9.0.0"

    def test_no_save_on_exception(self, pkgbuild) -> None:
        """with 块抛异常时不保存"""
        try:
            with PKGBUILDEditor(pkgbuild) as editor:
                editor.update_pkgver("9.0.0")
                raise RuntimeError("test error")
        except RuntimeError:
            pass

        # 重新加载验证未保存
        editor2 = PKGBUILDEditor(pkgbuild)
        assert editor2.get_pkgver() == "1.0.0"


class TestUpdateSourceArchEdgeCases:
    """update_source（arch 特定）替换逻辑的边界条件测试"""

    def _write(self, tmp_path: Path, body: str) -> Path:
        p = tmp_path / "PKGBUILD"
        p.write_text(body, encoding="utf-8")
        return p

    def test_braces_shell_var_in_url_skipped(self, tmp_path: Path) -> None:
        """URL 含 ${_gh}（花括号）时保留 shell 变量，不更新"""
        body = 'source_x86_64=("zen-${pkgver}.tar.xz::${_gh}/zen.tar.xz")\n'
        editor = PKGBUILDEditor(self._write(tmp_path, body))
        editor.update_source("https://new/file.tar.xz", arch="x86_64")
        assert "${_gh}/zen.tar.xz" in editor.content
        assert "https://new/file.tar.xz" not in editor.content

    def test_braceless_shell_var_in_url_skipped(self, tmp_path: Path) -> None:
        """URL 含 $_gh（无花括号）时同样应保留，等价于 ${_gh}"""
        body = 'source_x86_64=("zen-${pkgver}.tar.xz::$_gh/zen.tar.xz")\n'
        editor = PKGBUILDEditor(self._write(tmp_path, body))
        editor.update_source("https://new/file.tar.xz", arch="x86_64")
        assert "$_gh/zen.tar.xz" in editor.content
        assert "https://new/file.tar.xz" not in editor.content

    def test_alias_preserved_when_url_updated(self, tmp_path: Path) -> None:
        """别名含 ${pkgver}、URL 硬编码时，保留别名、替换 URL"""
        body = 'source_x86_64=("app-${pkgver}-${pkgrel}.tar.gz::https://old/file.tar.gz")\n'
        editor = PKGBUILDEditor(self._write(tmp_path, body))
        editor.update_source("https://new/file.tar.gz", arch="x86_64")
        assert "app-${pkgver}-${pkgrel}.tar.gz::" in editor.content
        assert "https://new/file.tar.gz" in editor.content
        assert "https://old/file.tar.gz" not in editor.content

    def test_plain_url_without_alias_replaced(self, tmp_path: Path) -> None:
        """无别名的裸 URL 直接替换"""
        body = "source_x86_64=('https://old/file.deb')\n"
        editor = PKGBUILDEditor(self._write(tmp_path, body))
        editor.update_source("https://new/file.deb", arch="x86_64")
        assert "https://new/file.deb" in editor.content
        assert "https://old/file.deb" not in editor.content

    def test_multientry_line_preserves_local_sources(self, tmp_path: Path) -> None:
        """单行多条目：替换远程 URL，保留本地源文件"""
        body = 'source_x86_64=("launcher.sh" "app::https://old/file.tar.gz")\n'
        editor = PKGBUILDEditor(self._write(tmp_path, body))
        editor.update_source("https://new/file.tar.gz", arch="x86_64")
        assert "launcher.sh" in editor.content
        assert "app::https://new/file.tar.gz" in editor.content
        assert "https://old/file.tar.gz" not in editor.content

    def test_multiline_array_url_updated(self, tmp_path: Path) -> None:
        """多行数组：正确更新 URL，不破坏结构"""
        body = 'source_x86_64=(\n    "app::https://old/file.tar.gz"\n)\n'
        editor = PKGBUILDEditor(self._write(tmp_path, body))
        editor.update_source("https://new/file.tar.gz", arch="x86_64")
        assert "https://new/file.tar.gz" in editor.content
        assert "https://old/file.tar.gz" not in editor.content

    def test_missing_source_arch_field_is_noop(self, tmp_path: Path) -> None:
        """缺失 source_<arch> 字段时不破坏其它内容"""
        body = "pkgname=test\npkgver=1.0.0\nsource=('launcher.sh')\n"
        editor = PKGBUILDEditor(self._write(tmp_path, body))
        original = editor.content
        editor.update_source("https://new/file.tar.gz", arch="x86_64")
        assert editor.content == original

    def test_indented_source_line_is_noop(self, tmp_path: Path) -> None:
        """缩进的 source 行（不在行首）不被匹配，保持原样"""
        body = '  source_x86_64=("app::https://old/file.tar.gz")\n'
        editor = PKGBUILDEditor(self._write(tmp_path, body))
        original = editor.content
        editor.update_source("https://new/file.tar.gz", arch="x86_64")
        assert editor.content == original

    def test_empty_source_array_left_untouched(self, tmp_path: Path) -> None:
        """空 source 数组不应被填入 URL，保持为空"""
        body = "source_x86_64=()\n"
        editor = PKGBUILDEditor(self._write(tmp_path, body))
        original = editor.content
        editor.update_source("https://new/file.tar.gz", arch="x86_64")
        assert editor.content == original

    def test_duplicate_source_lines_updates_first_only(self, tmp_path: Path) -> None:
        """重复的 source_<arch> 行只更新第一处，第二处保留原样"""
        body = (
            'source_x86_64=("a::https://old/1.tar.gz")\n'
            'source_x86_64=("b::https://old/2.tar.gz")\n'
        )
        editor = PKGBUILDEditor(self._write(tmp_path, body))
        editor.update_source("https://new/file.tar.gz", arch="x86_64")
        assert "a::https://new/file.tar.gz" in editor.content
        assert "b::https://old/2.tar.gz" in editor.content

    def test_alias_containing_double_colon_splits_at_first(self, tmp_path: Path) -> None:
        """别名含 :: 时按 makepkg 语义在首个 :: 处分隔"""
        body = 'source_x86_64=("weird::name::https://old/file.tar.gz")\n'
        editor = PKGBUILDEditor(self._write(tmp_path, body))
        editor.update_source("https://new/file.tar.gz", arch="x86_64")
        # makepkg 把首个 :: 左侧当文件名，故 alias="weird"
        assert '"weird::https://new/file.tar.gz"' in editor.content

    def test_backslash_in_new_url_does_not_crash(self, tmp_path: Path) -> None:
        """new_url 含反斜杠（如 \1）时不应触发 re.sub 反向引用崩溃"""
        body = 'source_x86_64=("app::https://old/file.tar.gz")\n'
        editor = PKGBUILDEditor(self._write(tmp_path, body))
        editor.update_source(r"https://new/\1file.tar.gz", arch="x86_64")
        assert "https://new/" in editor.content

    def test_backslash_in_alias_does_not_crash(self, tmp_path: Path) -> None:
        """alias 含反斜杠（来自文件内容）时不应崩溃"""
        body = 'source_x86_64=("app\\1::https://old/file.tar.gz")\n'
        editor = PKGBUILDEditor(self._write(tmp_path, body))
        editor.update_source("https://new/file.tar.gz", arch="x86_64")
        assert "https://new/file.tar.gz" in editor.content


class TestUpdateSourceEdgeCases:
    """update_source（arch=None，arch='any' 包）行为测试"""

    def _write(self, tmp_path: Path, body: str) -> Path:
        p = tmp_path / "PKGBUILD"
        p.write_text(body, encoding="utf-8")
        return p

    def test_braces_shell_var_in_url_skipped(self, tmp_path: Path) -> None:
        """any 包：URL 含 ${_gh} 时保留 shell 变量（与架构特定方法一致）"""
        body = 'source=("${pkgver}::${_gh}/file.tar.xz")\n'
        editor = PKGBUILDEditor(self._write(tmp_path, body))
        editor.update_source("https://new/file.tar.xz")
        assert "${_gh}/file.tar.xz" in editor.content
        assert "https://new/file.tar.xz" not in editor.content

    def test_alias_preserved_when_url_updated(self, tmp_path: Path) -> None:
        """any 包：保留别名、替换 URL"""
        body = 'source=("app-${pkgver}::https://old/file.tar.gz")\n'
        editor = PKGBUILDEditor(self._write(tmp_path, body))
        editor.update_source("https://new/file.tar.gz")
        assert "app-${pkgver}::" in editor.content
        assert "https://new/file.tar.gz" in editor.content
        assert "https://old/file.tar.gz" not in editor.content

    def test_multientry_preserves_local_sources(self, tmp_path: Path) -> None:
        """any 包：多条目保留本地源"""
        body = 'source=("launcher.sh" "app::https://old/file.tar.gz")\n'
        editor = PKGBUILDEditor(self._write(tmp_path, body))
        editor.update_source("https://new/file.tar.gz")
        assert "launcher.sh" in editor.content
        assert "app::https://new/file.tar.gz" in editor.content
