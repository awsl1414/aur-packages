"""ApiParser 单元测试

数据源：``aur-packages-helper`` 的 ``GET /api/v1/packages/{name}`` 接口。
响应格式见 ``parsers/api_parser.py`` 模块文档字符串。
"""

import json

from parsers.api_parser import ApiParser

# 完整合法的 API 响应：含 code / message / data(version + urls + hashes)
API_RESPONSE: dict = {
    "code": 0,
    "message": "ok",
    "data": {
        "name": "navicat",
        "version": "17.3.10",
        "urls": {
            "x86_64": "https://dn.navicat.com/download/navicat17-premium-cs-x86_64.AppImage",
            "aarch64": "https://dn.navicat.com/download/navicat17-premium-cs-aarch64.AppImage",
        },
        "hashes": {
            "x86_64": "c633020961f2fabe7a37f5998f41644ec425010d98ef75ae42bce0e3cbd7488691b93740f1123c12a4a28cd65022f596bc5fb3c0bd3dd1acdf040cb29d53489f",
            "aarch64": "a0891e62a0d9fa4613afc21e5fd2d91020a48723cc1993ca5fa8827abd362d601463e7eab446ed8ff5f56abe9c8a7276f7a63808f97b5a4171cdbf71bc3897c5",
        },
    },
}


class TestApiParseSuccess:
    def test_valid_response(self) -> None:
        parser = ApiParser()
        parsed = parser.parse(json.dumps(API_RESPONSE))
        assert parsed is not None
        assert parsed.version == "17.3.10"
        assert set(parsed.urls.keys()) == {"x86_64", "aarch64"}
        assert parsed.urls["x86_64"].endswith(".AppImage")
        assert set(parsed.hashes.keys()) == {"x86_64", "aarch64"}
        assert parsed.hashes["x86_64"] == API_RESPONSE["data"]["hashes"]["x86_64"]

    def test_urls_values_preserved(self) -> None:
        parser = ApiParser()
        parsed = parser.parse(json.dumps(API_RESPONSE))
        assert parsed is not None
        for arch in ("x86_64", "aarch64"):
            assert parsed.urls[arch] == API_RESPONSE["data"]["urls"][arch]


class TestApiParseVersionFailures:
    def test_non_string_input(self) -> None:
        parser = ApiParser()
        assert parser.parse(None) is None  # type: ignore
        assert parser.parse(123) is None  # type: ignore

    def test_invalid_json(self) -> None:
        parser = ApiParser()
        assert parser.parse("not json") is None

    def test_non_zero_code(self) -> None:
        """API 返回 code != 0 时返回 None"""
        parser = ApiParser()
        data = {"code": 1, "message": "error", "data": {"version": "1.0"}}
        assert parser.parse(json.dumps(data)) is None

    def test_missing_data_section(self) -> None:
        parser = ApiParser()
        assert parser.parse('{"code": 0}') is None
        assert parser.parse('{"code": 0, "data": "not a dict"}') is None

    def test_missing_version_field(self) -> None:
        """data 段中无 version 字段时返回 None"""
        parser = ApiParser()
        data = {"code": 0, "data": {"urls": {"x86_64": "https://example.com"}}}
        assert parser.parse(json.dumps(data)) is None

    def test_empty_version(self) -> None:
        """version 为空字符串时返回 None"""
        parser = ApiParser()
        data = {"code": 0, "data": {"version": ""}}
        assert parser.parse(json.dumps(data)) is None


class TestApiParseUrls:
    def test_missing_urls_field(self) -> None:
        parser = ApiParser()
        data = {"code": 0, "data": {"version": "1.0"}}
        assert parser.parse(json.dumps(data)) is None

    def test_empty_urls(self) -> None:
        """urls 为空字典（无有效架构 URL）时返回 None"""
        parser = ApiParser()
        data = {"code": 0, "data": {"version": "1.0", "urls": {}}}
        assert parser.parse(json.dumps(data)) is None

    def test_non_string_url_value_skipped(self) -> None:
        """url 值非字符串时跳过该架构；仍有有效项则正常返回"""
        parser = ApiParser()
        data = {
            "code": 0,
            "data": {
                "version": "1.0",
                "urls": {"x86_64": 12345, "aarch64": "https://example.com/a"},
            },
        }
        parsed = parser.parse(json.dumps(data))
        assert parsed is not None
        assert set(parsed.urls.keys()) == {"aarch64"}


class TestApiParseHashes:
    def test_missing_hashes_field_returns_empty(self) -> None:
        """data 中无 hashes 字段时 hashes 为空字典（调用方回退下载），不算解析失败"""
        parser = ApiParser()
        data = {"code": 0, "data": {"version": "1.0", "urls": {"x86_64": "https://x"}}}
        parsed = parser.parse(json.dumps(data))
        assert parsed is not None
        assert parsed.hashes == {}

    def test_empty_hashes(self) -> None:
        """hashes 为空字典时正常返回，hashes 为空"""
        parser = ApiParser()
        data = {
            "code": 0,
            "data": {"version": "1.0", "urls": {"x86_64": "https://x"}, "hashes": {}},
        }
        parsed = parser.parse(json.dumps(data))
        assert parsed is not None
        assert parsed.hashes == {}

    def test_none_hash_value_skipped(self) -> None:
        """hash 值为 None（helper schema 允许）时跳过该架构"""
        parser = ApiParser()
        data = {
            "code": 0,
            "data": {
                "version": "1.0",
                "urls": {"x86_64": "https://x", "aarch64": "https://a"},
                "hashes": {"x86_64": None, "aarch64": "valid_hash"},
            },
        }
        parsed = parser.parse(json.dumps(data))
        assert parsed is not None
        assert parsed.hashes == {"aarch64": "valid_hash"}

    def test_empty_hash_string_skipped(self) -> None:
        """空字符串 hash 被跳过"""
        parser = ApiParser()
        data = {
            "code": 0,
            "data": {
                "version": "1.0",
                "urls": {"x86_64": "https://x", "aarch64": "https://a"},
                "hashes": {"x86_64": "", "aarch64": "valid_hash"},
            },
        }
        parsed = parser.parse(json.dumps(data))
        assert parsed is not None
        assert parsed.hashes == {"aarch64": "valid_hash"}
