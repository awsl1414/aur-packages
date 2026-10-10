"""URL 工具函数单元测试"""

from aur_auto_update.utils.url_utils import (
    extract_extension_from_url,
    extract_filename_from_url,
    generate_download_filename,
)


class TestExtractFilenameFromUrl:
    def test_simple_url(self) -> None:
        assert extract_filename_from_url("https://example.com/file.deb") == "file.deb"

    def test_query_params(self) -> None:
        assert (
            extract_filename_from_url("https://example.com/file.deb?v=1&k=2")
            == "file.deb"
        )

    def test_fragment(self) -> None:
        assert (
            extract_filename_from_url("https://example.com/file.deb#section")
            == "file.deb"
        )

    def test_encoded_spaces(self) -> None:
        assert (
            extract_filename_from_url("https://example.com/Trae%20CN-linux-x64.tar.gz")
            == "Trae%20CN-linux-x64.tar.gz"
        )


class TestExtractExtensionFromUrl:
    def test_deb(self) -> None:
        assert extract_extension_from_url("https://example.com/file.deb") == ".deb"

    def test_tar_gz(self) -> None:
        assert (
            extract_extension_from_url("https://example.com/file.tar.gz") == ".tar.gz"
        )

    def test_tar_xz(self) -> None:
        assert (
            extract_extension_from_url("https://example.com/file.tar.xz") == ".tar.xz"
        )

    def test_appimage(self) -> None:
        assert (
            extract_extension_from_url("https://example.com/app.AppImage")
            == ".AppImage"
        )

    def test_no_extension(self) -> None:
        assert extract_extension_from_url("https://example.com/file") == ""


class TestGenerateDownloadFilename:
    def test_deb_extension(self) -> None:
        result = generate_download_filename(
            "qq", "3.2.28", "x86_64", "https://example.com/QQ_amd64.deb"
        )
        assert result == "qq_3.2.28_x86_64.deb"

    def test_tar_gz_extension(self) -> None:
        result = generate_download_filename(
            "trae", "2.3.25937", "x86_64", "https://example.com/Trae-linux-x64.tar.gz"
        )
        assert result == "trae_2.3.25937_x86_64.tar.gz"

    def test_default_extension(self) -> None:
        result = generate_download_filename(
            "pkg", "1.0", "x86_64", "https://example.com/file", default_extension=".bin"
        )
        assert result == "pkg_1.0_x86_64.bin"


class TestFilenameSanitization:
    """组件白名单清洗：防版本/包名串注入路径（version 来自上游响应）"""

    def test_path_traversal_sanitized(self) -> None:
        """version 携带路径分隔符被替换，文件名不逃出下载目录"""
        result = generate_download_filename(
            "pkg", "../../etc/passwd", "x86_64", "https://example.com/f.deb"
        )
        assert "/" not in result and "\\" not in result
        assert result.endswith(".deb")

    def test_control_chars_sanitized(self) -> None:
        """version 携带换行等控制字符被替换"""
        result = generate_download_filename(
            "pkg", "1.0\n  dir=/tmp", "x86_64", "https://example.com/f"
        )
        assert "\n" not in result and "\r" not in result

    def test_valid_components_unchanged(self) -> None:
        """现有包的合法命名形态零变形"""
        assert (
            generate_download_filename(
                "bt-dualboot-ng", "1.2.3", "any", "https://example.com/f.zip"
            )
            == "bt-dualboot-ng_1.2.3_any.zip"
        )
        assert (
            generate_download_filename(
                "qq", "3.2.31_260710", "x86_64", "https://example.com/f.deb"
            )
            == "qq_3.2.31_260710_x86_64.deb"
        )
