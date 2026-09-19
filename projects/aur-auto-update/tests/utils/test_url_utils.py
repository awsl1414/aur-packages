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
