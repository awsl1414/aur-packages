"""QQParser 单元测试

数据源：第三方聚合 API ``http://ip.llz.asia:8000/api/v1/packages/qq``。
响应格式见 ``parsers/qq.py`` 模块文档字符串。
"""

import json

from constants.constants import ArchEnum
from parsers.qq import QQParser

# 完整合法的 API 响应：含 code / message / data(version + urls + hashes)
QQ_API_RESPONSE: dict = {
    "code": 0,
    "message": "ok",
    "data": {
        "name": "qq",
        "version": "3.2.31_260710",
        "urls": {
            "x86_64": "https://qqdl.gtimg.cn/qqfile/QQNTV2/9.9.32/release/c390e792/QQ_3.2.31_260710_amd64_01.deb",
            "aarch64": "https://qqdl.gtimg.cn/qqfile/QQNTV2/9.9.32/release/c390e792/QQ_3.2.31_260710_arm64_01.deb",
            "loong64": "https://qqdl.gtimg.cn/qqfile/QQNTV2/9.9.32/release/c390e792/QQ_3.2.31_260710_loongarch64_01.deb",
        },
        "hashes": {
            "x86_64": "234a0f338d47e952995a1d4cf1dc782e5266623f878b92af264753b8c032fd31450169e1e25c8d10d37e26848c28dbb0302732874bbfce1566f8ad2b89e0337b",
            "aarch64": "e31096831099d3a9285443e62344d7ec451a9b991283f803e568ae61ab578b3de79ffd6d2bfbf69923a62715428a13cfcd33e2682d4d873d38add44e66ddf135",
            "loong64": "ef51070de26b8f33fedb1f70abe3d348aef90b47405ac74f181dd696ce4288fcf657e4c13014807a1069b56a547ca4be64673cd05f9e7ddf62df2d445af8bb9d",
        },
    },
}


class TestQQParseVersion:
    def test_valid_response(self) -> None:
        parser = QQParser()
        response = json.dumps(QQ_API_RESPONSE)
        assert parser.parse_version(response) == "3.2.31_260710"

    def test_non_string_input(self) -> None:
        parser = QQParser()
        assert parser.parse_version(None) is None
        assert parser.parse_version(123) is None
        assert parser.parse_version({"code": 0}) is None

    def test_invalid_json(self) -> None:
        parser = QQParser()
        assert parser.parse_version("not json") is None

    def test_non_zero_code(self) -> None:
        """API 返回 code != 0 时返回 None"""
        parser = QQParser()
        data = {"code": 1, "message": "error", "data": {"version": "1.0"}}
        assert parser.parse_version(json.dumps(data)) is None

    def test_missing_data_section(self) -> None:
        parser = QQParser()
        assert parser.parse_version('{"code": 0}') is None
        assert parser.parse_version('{"code": 0, "data": "not a dict"}') is None

    def test_missing_version_field(self) -> None:
        """data 段中无 version 字段时返回 None"""
        parser = QQParser()
        data = {"code": 0, "data": {"urls": {}}}
        assert parser.parse_version(json.dumps(data)) is None

    def test_empty_version(self) -> None:
        """version 为空字符串时返回 None"""
        parser = QQParser()
        data = {"code": 0, "data": {"version": ""}}
        assert parser.parse_version(json.dumps(data)) is None


class TestQQParseUrl:
    def test_x86_64(self) -> None:
        parser = QQParser()
        response = json.dumps(QQ_API_RESPONSE)
        url = parser.parse_url(ArchEnum.X86_64, response)
        assert url is not None
        assert "amd64" in url
        assert url.endswith(".deb")

    def test_aarch64(self) -> None:
        parser = QQParser()
        response = json.dumps(QQ_API_RESPONSE)
        url = parser.parse_url(ArchEnum.AARCH64, response)
        assert url is not None
        assert "arm64" in url
        assert url.endswith(".deb")

    def test_loong64(self) -> None:
        parser = QQParser()
        response = json.dumps(QQ_API_RESPONSE)
        url = parser.parse_url(ArchEnum.LOONG64, response)
        assert url is not None
        assert "loongarch64" in url
        assert url.endswith(".deb")

    def test_non_string_input(self) -> None:
        parser = QQParser()
        assert parser.parse_url(ArchEnum.X86_64, None) is None
        assert parser.parse_url(ArchEnum.X86_64, 123) is None

    def test_invalid_json(self) -> None:
        parser = QQParser()
        assert parser.parse_url(ArchEnum.X86_64, "not json") is None

    def test_non_zero_code(self) -> None:
        parser = QQParser()
        data = {"code": 1, "data": {"urls": {"x86_64": "https://example.com"}}}
        assert parser.parse_url(ArchEnum.X86_64, json.dumps(data)) is None

    def test_missing_urls_field(self) -> None:
        parser = QQParser()
        data = {"code": 0, "data": {"version": "1.0"}}
        assert parser.parse_url(ArchEnum.X86_64, json.dumps(data)) is None

    def test_unknown_arch(self) -> None:
        """请求未在 API urls 中的架构时返回 None"""
        parser = QQParser()
        response = json.dumps(QQ_API_RESPONSE)
        assert parser.parse_url("riscv64", response) is None

    def test_arch_value_as_string(self) -> None:
        """直接用字符串传入架构名也能正确取到 URL"""
        parser = QQParser()
        response = json.dumps(QQ_API_RESPONSE)
        url = parser.parse_url("x86_64", response)
        assert url is not None
        assert "amd64" in url


class TestQQParseHashes:
    def test_returns_all_arch_hashes(self) -> None:
        parser = QQParser()
        response = json.dumps(QQ_API_RESPONSE)
        archs = [ArchEnum.X86_64, ArchEnum.AARCH64, ArchEnum.LOONG64]
        result = parser.parse_hashes(response, archs)
        assert result is not None
        assert set(result.keys()) == {"x86_64", "aarch64", "loong64"}
        for arch_value in ("x86_64", "aarch64", "loong64"):
            assert result[arch_value] == QQ_API_RESPONSE["data"]["hashes"][arch_value]

    def test_partial_archs(self) -> None:
        """只请求部分架构时只返回这部分 hash"""
        parser = QQParser()
        response = json.dumps(QQ_API_RESPONSE)
        result = parser.parse_hashes(response, [ArchEnum.X86_64])
        assert result is not None
        assert list(result.keys()) == ["x86_64"]

    def test_missing_some_arch_hash(self) -> None:
        """API 缺少部分架构 hash 时，只返回存在的部分"""
        parser = QQParser()
        data = {
            "code": 0,
            "data": {
                "version": "1.0",
                "urls": {"x86_64": "https://example.com/a.deb"},
                "hashes": {"x86_64": "abc123"},
            },
        }
        response = json.dumps(data)
        result = parser.parse_hashes(
            response, [ArchEnum.X86_64, ArchEnum.AARCH64]
        )
        assert result is not None
        assert result == {"x86_64": "abc123"}

    def test_missing_hashes_field(self) -> None:
        """data 中无 hashes 字段时返回 None（fallback 到下载）"""
        parser = QQParser()
        data = {"code": 0, "data": {"version": "1.0", "urls": {}}}
        response = json.dumps(data)
        result = parser.parse_hashes(response, [ArchEnum.X86_64])
        assert result is None

    def test_empty_hashes_when_no_arch_matched(self) -> None:
        """所有架构 hash 都缺失时返回 None"""
        parser = QQParser()
        data = {
            "code": 0,
            "data": {"version": "1.0", "urls": {}, "hashes": {}},
        }
        response = json.dumps(data)
        result = parser.parse_hashes(response, [ArchEnum.X86_64])
        assert result is None

    def test_non_string_input(self) -> None:
        parser = QQParser()
        assert parser.parse_hashes(None, [ArchEnum.X86_64]) is None
        assert parser.parse_hashes(123, [ArchEnum.X86_64]) is None

    def test_invalid_json(self) -> None:
        parser = QQParser()
        assert parser.parse_hashes("not json", [ArchEnum.X86_64]) is None

    def test_non_zero_code(self) -> None:
        parser = QQParser()
        data = {
            "code": 1,
            "data": {"hashes": {"x86_64": "abc"}},
        }
        response = json.dumps(data)
        assert parser.parse_hashes(response, [ArchEnum.X86_64]) is None

    def test_non_string_hash_value(self) -> None:
        """hash 值非字符串时跳过该架构"""
        parser = QQParser()
        data = {
            "code": 0,
            "data": {
                "version": "1.0",
                "urls": {},
                "hashes": {"x86_64": 12345, "aarch64": "valid_hash"},
            },
        }
        response = json.dumps(data)
        result = parser.parse_hashes(
            response, [ArchEnum.X86_64, ArchEnum.AARCH64]
        )
        assert result is not None
        assert result == {"aarch64": "valid_hash"}

    def test_empty_hash_string_skipped(self) -> None:
        """空字符串 hash 被跳过"""
        parser = QQParser()
        data = {
            "code": 0,
            "data": {
                "version": "1.0",
                "urls": {},
                "hashes": {"x86_64": "", "aarch64": "valid_hash"},
            },
        }
        response = json.dumps(data)
        result = parser.parse_hashes(
            response, [ArchEnum.X86_64, ArchEnum.AARCH64]
        )
        assert result is not None
        assert result == {"aarch64": "valid_hash"}


class TestQQResolveUrl:
    """QQ 现在走聚合 API，原始 URL 即可直接下载——resolve_url 应与 parse_url 一致"""

    def test_resolve_equals_parse(self) -> None:
        parser = QQParser()
        response = json.dumps(QQ_API_RESPONSE)
        for arch in [ArchEnum.X86_64, ArchEnum.AARCH64, ArchEnum.LOONG64]:
            assert parser.resolve_url(arch, response) == parser.parse_url(
                arch, response
            )

    def test_unknown_arch_returns_none(self) -> None:
        parser = QQParser()
        response = json.dumps(QQ_API_RESPONSE)
        assert parser.resolve_url("riscv64", response) is None
