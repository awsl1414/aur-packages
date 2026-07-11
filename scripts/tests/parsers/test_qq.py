"""QQParser 单元测试"""

import json
from unittest.mock import MagicMock, patch

import httpx

from constants.constants import DEFAULT_TIMEOUT, USER_AGENT, ArchEnum
from parsers.qq import COOKIE_URL, QQParser, SIGN_URL

# 模拟 pcConfig.json 的最新响应：Linux 段下含 x64/armDownloadUrl（dict 含 deb），
# loongarch/mipsDownloadUrl 为裸字符串
QQ_JSON_RESPONSE: dict = {
    "Windows": {
        "version": "9.9.31",
        "updateDate": "2026-05-28",
    },
    "Linux": {
        "version": "3.2.31",
        "updateDate": "2026-07-10",
        "x64DownloadUrl": {
            "deb": "https://qqdl.gtimg.cn/qqfile/QQNTV2/9.9.32/release/c390e792/QQ_3.2.31_260710_amd64_01.deb",
            "appimage": "https://qqdl.gtimg.cn/qqfile/QQNTV2/9.9.32/release/c390e792/QQ_3.2.31_260710_x86_64_01.AppImage",
            "rpm": "https://qqdl.gtimg.cn/qqfile/QQNTV2/9.9.32/release/c390e792/QQ_3.2.31_260710_x86_64_01.rpm",
        },
        "armDownloadUrl": {
            "deb": "https://qqdl.gtimg.cn/qqfile/QQNTV2/9.9.32/release/c390e792/QQ_3.2.31_260710_arm64_01.deb",
            "rpm": "https://qqdl.gtimg.cn/qqfile/QQNTV2/9.9.32/release/c390e792/QQ_3.2.31_260710_aarch64_01.rpm",
            "appimage": "https://qqdl.gtimg.cn/qqfile/QQNTV2/9.9.32/release/c390e792/QQ_3.2.31_260710_arm64_01.AppImage",
        },
        "loongarchDownloadUrl": "https://qqdl.gtimg.cn/qqfile/QQNTV2/9.9.32/release/c390e792/QQ_3.2.31_260710_loongarch64_01.deb",
        "mipsDownloadUrl": "https://qqdl.gtimg.cn/qqfile/QQNTV2/9.9.32/release/c390e792/QQ_3.2.31_260710_mips64el_01.deb",
    },
    "macOS": {
        "version": "6.9.98 (Intel+Apple Silicon)",
        "updateDate": "2026-07-10",
    },
}


class TestQQParseVersion:
    def test_valid_json(self) -> None:
        parser = QQParser()
        response = json.dumps(QQ_JSON_RESPONSE)
        assert parser.parse_version(response) == "3.2.31_260710"

    def test_non_string_input(self) -> None:
        parser = QQParser()
        assert parser.parse_version(None) is None
        assert parser.parse_version(123) is None
        assert parser.parse_version({"Linux": {"version": "1.0"}}) is None

    def test_invalid_json(self) -> None:
        parser = QQParser()
        assert parser.parse_version("not json") is None

    def test_missing_linux_section(self) -> None:
        parser = QQParser()
        assert parser.parse_version('{"Windows": {}}') is None

    def test_missing_version_field(self) -> None:
        parser = QQParser()
        data = {
            "Linux": {
                "x64DownloadUrl": {
                    "deb": "https://example.com/QQ_1.0.0_123_amd64_01.deb"
                }
            }
        }
        assert parser.parse_version(json.dumps(data)) is None

    def test_version_mismatch(self) -> None:
        """Linux.version 与 URL 中的版本号不一致时返回 None"""
        parser = QQParser()
        data = {
            "Linux": {
                "version": "3.2.30",
                "x64DownloadUrl": {
                    "deb": "https://example.com/QQ_3.2.31_260710_amd64_01.deb"
                },
            }
        }
        assert parser.parse_version(json.dumps(data)) is None

    def test_url_missing_build_number(self) -> None:
        """URL 中没有构建号时返回 None"""
        parser = QQParser()
        data = {
            "Linux": {
                "version": "3.2.31",
                "x64DownloadUrl": {
                    "deb": "https://example.com/QQ_3.2.31_amd64_01.deb"
                },
            }
        }
        assert parser.parse_version(json.dumps(data)) is None

    def test_url_field_is_string(self) -> None:
        """x64DownloadUrl 为裸字符串（非 dict）时返回 None"""
        parser = QQParser()
        data = {
            "Linux": {
                "version": "3.2.31",
                "x64DownloadUrl": "https://example.com/QQ_3.2.31_260710_amd64_01.deb",
            }
        }
        assert parser.parse_version(json.dumps(data)) is None


class TestQQParseUrl:
    def test_x86_64(self) -> None:
        parser = QQParser()
        response = json.dumps(QQ_JSON_RESPONSE)
        url = parser.parse_url(ArchEnum.X86_64, response)
        assert url is not None
        assert "amd64" in url
        assert url.endswith(".deb")
        assert "260710" in url

    def test_aarch64(self) -> None:
        parser = QQParser()
        response = json.dumps(QQ_JSON_RESPONSE)
        url = parser.parse_url(ArchEnum.AARCH64, response)
        assert url is not None
        assert "arm64" in url
        assert url.endswith(".deb")

    def test_loong64(self) -> None:
        parser = QQParser()
        response = json.dumps(QQ_JSON_RESPONSE)
        url = parser.parse_url(ArchEnum.LOONG64, response)
        assert url is not None
        assert "loongarch64" in url
        assert url.endswith(".deb")

    def test_mips64el(self) -> None:
        parser = QQParser()
        response = json.dumps(QQ_JSON_RESPONSE)
        url = parser.parse_url(ArchEnum.MIPS64EL, response)
        assert url is not None
        assert "mips64el" in url
        assert url.endswith(".deb")

    def test_non_string_input(self) -> None:
        parser = QQParser()
        assert parser.parse_url(ArchEnum.X86_64, None) is None
        assert parser.parse_url(ArchEnum.X86_64, 123) is None

    def test_invalid_json(self) -> None:
        parser = QQParser()
        assert parser.parse_url(ArchEnum.X86_64, "not json") is None

    def test_missing_linux_section(self) -> None:
        parser = QQParser()
        assert parser.parse_url(ArchEnum.X86_64, '{"Windows": {}}') is None

    def test_unknown_arch(self) -> None:
        """未知架构返回 None（由 _get_deb_url 的 match 默认分支返回）"""
        parser = QQParser()
        response = json.dumps(QQ_JSON_RESPONSE)
        # 通过字符串传入未知架构（绕过 ArchEnum 校验）
        assert parser.parse_url("riscv64", response) is None


def _make_cookie_response(cookie_value: str | None) -> MagicMock:
    """构造模拟 im.qq.com/index/ 的 cookie 响应"""
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.cookies.get = MagicMock(return_value=cookie_value)
    return resp


def _make_sign_response(
    body: object, *, raises: bool = False
) -> MagicMock:
    """构造模拟 GetSign 响应"""
    resp = MagicMock()
    if raises:
        resp.raise_for_status = MagicMock(side_effect=Exception("HTTP error"))
    else:
        resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=body)
    return resp


class TestQQResolveUrl:
    """resolve_url 测试：mock httpx.Client 验证 URL 签名流程"""

    def test_returns_signed_url(self) -> None:
        """正常流程：返回 GetSign data.url"""
        original_url = (
            "https://qqdl.gtimg.cn/qqfile/QQNTV2/9.9.32/release/"
            "c390e792/QQ_3.2.31_260710_amd64_01.deb"
        )
        signed_url = original_url + "?sign=abc123&t=1700000000"

        cookie_resp = _make_cookie_response("dd315a3e7f4613df13ad03ceb8eebf38")
        sign_resp = _make_sign_response(
            {"retcode": 0, "data": {"url": signed_url}}
        )

        with patch("parsers.qq.httpx.Client") as client_cls:
            client = MagicMock()
            client.__enter__ = MagicMock(return_value=client)
            client.__exit__ = MagicMock(return_value=False)
            client.get = MagicMock(return_value=cookie_resp)
            client.post = MagicMock(return_value=sign_resp)
            client_cls.return_value = client

            parser = QQParser()
            result = parser.resolve_url(ArchEnum.X86_64, json.dumps(QQ_JSON_RESPONSE))

        assert result == signed_url
        # 验证 cookie 请求 URL
        client.get.assert_called_once()
        assert client.get.call_args.args[0] == COOKIE_URL
        assert client.get.call_args.kwargs["headers"]["User-Agent"] == USER_AGENT
        # 验证 GetSign 请求 URL 与 body
        client.post.assert_called_once()
        call_kwargs = client.post.call_args.kwargs
        assert client.post.call_args.args[0] == SIGN_URL
        assert call_kwargs["json"] == {"url": original_url}
        assert call_kwargs["cookies"] == {
            "tgw_l7_route": "dd315a3e7f4613df13ad03ceb8eebf38"
        }
        assert call_kwargs["headers"]["x-oidb"] == (
            '{"uint32_command":"0x9b8e","uint32_service_type":1}'
        )
        # 验证 DEFAULT_TIMEOUT 已应用到 httpx.Client
        client_cls.assert_called_once_with(timeout=DEFAULT_TIMEOUT)

    def test_returns_none_when_no_parse_url(self) -> None:
        """parse_url 返回 None 时，resolve_url 不调用网络，直接返回 None"""
        with patch("parsers.qq.httpx.Client") as client_cls:
            parser = QQParser()
            # 未知架构
            result = parser.resolve_url("riscv64", json.dumps(QQ_JSON_RESPONSE))
        assert result is None
        client_cls.assert_not_called()

    def test_returns_none_when_cookie_missing(self) -> None:
        """cookie 响应中无 tgw_l7_route 时返回 None"""
        cookie_resp = _make_cookie_response(None)
        with patch("parsers.qq.httpx.Client") as client_cls:
            client = MagicMock()
            client.__enter__ = MagicMock(return_value=client)
            client.__exit__ = MagicMock(return_value=False)
            client.get = MagicMock(return_value=cookie_resp)
            client.post = MagicMock()
            client_cls.return_value = client

            parser = QQParser()
            result = parser.resolve_url(
                ArchEnum.X86_64, json.dumps(QQ_JSON_RESPONSE)
            )

        assert result is None
        client.post.assert_not_called()

    def test_returns_none_when_response_invalid(self) -> None:
        """GetSign 返回非 dict 时返回 None"""
        cookie_resp = _make_cookie_response("cookie_value")
        sign_resp = _make_sign_response(["not", "a", "dict"])
        with patch("parsers.qq.httpx.Client") as client_cls:
            client = MagicMock()
            client.__enter__ = MagicMock(return_value=client)
            client.__exit__ = MagicMock(return_value=False)
            client.get = MagicMock(return_value=cookie_resp)
            client.post = MagicMock(return_value=sign_resp)
            client_cls.return_value = client

            parser = QQParser()
            result = parser.resolve_url(
                ArchEnum.X86_64, json.dumps(QQ_JSON_RESPONSE)
            )

        assert result is None

    def test_returns_none_when_data_missing(self) -> None:
        """GetSign 响应中 data 不是 dict 时返回 None"""
        cookie_resp = _make_cookie_response("cookie_value")
        sign_resp = _make_sign_response({"data": "not a dict"})
        with patch("parsers.qq.httpx.Client") as client_cls:
            client = MagicMock()
            client.__enter__ = MagicMock(return_value=client)
            client.__exit__ = MagicMock(return_value=False)
            client.get = MagicMock(return_value=cookie_resp)
            client.post = MagicMock(return_value=sign_resp)
            client_cls.return_value = client

            parser = QQParser()
            result = parser.resolve_url(
                ArchEnum.X86_64, json.dumps(QQ_JSON_RESPONSE)
            )

        assert result is None

    def test_returns_none_when_url_missing(self) -> None:
        """GetSign 响应中 data.url 为空时返回 None"""
        cookie_resp = _make_cookie_response("cookie_value")
        sign_resp = _make_sign_response({"data": {"url": ""}})
        with patch("parsers.qq.httpx.Client") as client_cls:
            client = MagicMock()
            client.__enter__ = MagicMock(return_value=client)
            client.__exit__ = MagicMock(return_value=False)
            client.get = MagicMock(return_value=cookie_resp)
            client.post = MagicMock(return_value=sign_resp)
            client_cls.return_value = client

            parser = QQParser()
            result = parser.resolve_url(
                ArchEnum.X86_64, json.dumps(QQ_JSON_RESPONSE)
            )

        assert result is None

    def test_returns_none_on_http_error(self) -> None:
        """httpx.HTTPError 时返回 None"""
        cookie_resp = _make_cookie_response("cookie_value")
        sign_resp = _make_sign_response({})
        sign_resp.raise_for_status = MagicMock(
            side_effect=httpx.HTTPError("boom")
        )

        with patch("parsers.qq.httpx.Client") as client_cls:
            client = MagicMock()
            client.__enter__ = MagicMock(return_value=client)
            client.__exit__ = MagicMock(return_value=False)
            client.get = MagicMock(return_value=cookie_resp)
            client.post = MagicMock(return_value=sign_resp)
            client_cls.return_value = client

            parser = QQParser()
            result = parser.resolve_url(
                ArchEnum.X86_64, json.dumps(QQ_JSON_RESPONSE)
            )

        assert result is None

    def test_returns_none_on_invalid_json(self) -> None:
        """GetSign 响应非 JSON 时返回 None"""
        cookie_resp = _make_cookie_response("cookie_value")
        sign_resp = MagicMock()
        sign_resp.raise_for_status = MagicMock()
        sign_resp.json = MagicMock(side_effect=json.JSONDecodeError("", "", 0))
        with patch("parsers.qq.httpx.Client") as client_cls:
            client = MagicMock()
            client.__enter__ = MagicMock(return_value=client)
            client.__exit__ = MagicMock(return_value=False)
            client.get = MagicMock(return_value=cookie_resp)
            client.post = MagicMock(return_value=sign_resp)
            client_cls.return_value = client

            parser = QQParser()
            result = parser.resolve_url(
                ArchEnum.X86_64, json.dumps(QQ_JSON_RESPONSE)
            )

        assert result is None
