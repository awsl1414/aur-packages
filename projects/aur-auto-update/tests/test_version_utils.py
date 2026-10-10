"""版本比较工具单元测试"""

from aur_auto_update.utils.version_utils import compare_versions, parse_version


class TestParseVersion:
    def test_standard(self) -> None:
        assert parse_version("3.2.22") == ["3", "2", "22"]

    def test_with_build_number(self) -> None:
        assert parse_version("3.2.22_251203") == ["3", "2", "22", "251203"]

    def test_v_prefix(self) -> None:
        assert parse_version("v1.2.3") == ["1", "2", "3"]

    def test_r_prefix(self) -> None:
        assert parse_version("R4.5.6") == ["4", "5", "6"]

    def test_dash_separator(self) -> None:
        assert parse_version("1-2-3") == ["1", "2", "3"]

    def test_tilde_separator(self) -> None:
        assert parse_version("1~2~3") == ["1", "2", "3"]


class TestCompareVersions:
    def test_newer(self) -> None:
        assert compare_versions("3.2.23", "3.2.22") == 1

    def test_older(self) -> None:
        assert compare_versions("3.2.21", "3.2.22") == -1

    def test_equal(self) -> None:
        assert compare_versions("3.2.22", "3.2.22") == 0

    def test_with_build_number_newer(self) -> None:
        assert compare_versions("3.2.22_251203", "3.2.22") == 1

    def test_different_length(self) -> None:
        assert compare_versions("17.3", "17.3.0") == 0

    def test_major_version_difference(self) -> None:
        assert compare_versions("4.0.0", "3.99.99") == 1
