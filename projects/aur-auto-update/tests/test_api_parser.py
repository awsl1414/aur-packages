"""ApiParser 单元测试

数据源：``aur-metadata`` 的 ``GET /api/v1/packages/{name}`` 接口。
响应格式见 ``parsers/api_parser.py`` 模块文档字符串。
"""

import json
from typing import Any

from aur_auto_update.parsers.api_parser import ApiParser

# 完整合法的 API 响应：含 code / message / data(version + urls + download_urls)
API_RESPONSE: dict[str, Any] = {
    "code": 0,
    "message": "ok",
    "data": {
        "name": "navicat",
        "version": "17.3.10",
        "urls": {
            "x86_64": "https://dn.navicat.com/download/navicat17-premium-cs-x86_64.AppImage",
            "aarch64": "https://dn.navicat.com/download/navicat17-premium-cs-aarch64.AppImage",
        },
        "download_urls": {
            "x86_64": "https://dn.navicat.com/download/signed/navicat17-premium-cs-x86_64.AppImage",
            "aarch64": None,  # 该架构签名失败
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
        # download_urls 中 null 值架构被过滤
        assert parsed.download_urls == {"x86_64": API_RESPONSE["data"]["download_urls"]["x86_64"]}

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
                "download_urls": {},
            },
        }
        parsed = parser.parse(json.dumps(data))
        assert parsed is not None
        assert set(parsed.urls.keys()) == {"aarch64"}


class TestApiParseDownloadUrls:
    def test_missing_download_urls_field_fails(self) -> None:
        """缺少 download_urls 字段属响应契约违规 → 解析失败返回 None"""
        parser = ApiParser()
        data = {"code": 0, "data": {"version": "1.0", "urls": {"x86_64": "https://x"}}}
        assert parser.parse(json.dumps(data)) is None

    def test_non_string_url_value_skipped(self) -> None:
        """download_urls 值非字符串（如 null / 数字）时跳过该架构"""
        parser = ApiParser()
        data = {
            "code": 0,
            "data": {
                "version": "1.0",
                "urls": {"x86_64": "https://x", "aarch64": "https://a"},
                "download_urls": {"x86_64": 12345, "aarch64": "https://signed/a"},
            },
        }
        parsed = parser.parse(json.dumps(data))
        assert parsed is not None
        assert parsed.download_urls == {"aarch64": "https://signed/a"}

    def test_empty_string_url_value_skipped(self) -> None:
        """空字符串 download_urls 值被跳过"""
        parser = ApiParser()
        data = {
            "code": 0,
            "data": {
                "version": "1.0",
                "urls": {"x86_64": "https://x", "aarch64": "https://a"},
                "download_urls": {"x86_64": "", "aarch64": "https://signed/a"},
            },
        }
        parsed = parser.parse(json.dumps(data))
        assert parsed is not None
        assert parsed.download_urls == {"aarch64": "https://signed/a"}

    def test_empty_download_urls_dict(self) -> None:
        """download_urls 为空字典时正常返回（全部架构回退 urls 下载）"""
        parser = ApiParser()
        data = {
            "code": 0,
            "data": {
                "version": "1.0",
                "urls": {"x86_64": "https://x"},
                "download_urls": {},
            },
        }
        parsed = parser.parse(json.dumps(data))
        assert parsed is not None
        assert parsed.download_urls == {}
