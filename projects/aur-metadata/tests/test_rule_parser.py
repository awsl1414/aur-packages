"""aur_metadata.parsers.rule 单元测试"""


import json
import logging
from pathlib import Path
from typing import Any, cast

import pytest

from aur_metadata.constants import ArchEnum
from aur_metadata.parsers.rule import RuleDebParser, RuleParser, UrlRuleMap
from tests.fakes import build_deb, make_app_config

_APP_CONFIG = make_app_config()

# 真实 Navicat release-note 页面片段（含 platform="L" 表与 note-title 结构）
_NAVICAT_HTML: str = (
    Path(__file__).parent.joinpath("fixtures", "navicat_release_note.html")
    .read_text(encoding="utf-8")
)

# 真实 ZCode 官网下载区片段（含 Linux x64 .deb/.rpm/AppImage 直链）
_ZCODE_HTML: str = (
    Path(__file__).parent.joinpath("fixtures", "zcode_cn_download.html")
    .read_text(encoding="utf-8")
)

# packages.toml 中 zcode 包的生产规则（rule-deb：URL 以自校验的文件名为锚，
# 版本走 deb 头部权威提取，不配 version 规则）
_ZCODE_URL_X86_64_RULE: dict[str, Any] = {
    "kind": "re",
    "expr": r"https://[^\"<>\s]+/ZCode-[0-9]+(?:\.[0-9]+)+-linux-x64\.deb",
}
_ZCODE_URL_AARCH64_RULE: dict[str, Any] = {
    "kind": "re",
    "expr": r"https://[^\"<>\s]+/ZCode-[0-9]+(?:\.[0-9]+)+-linux-arm64\.deb",
}

# 真实 GitHub Releases API 响应（orca latest）：含 rpm / AppImage / server tarball
# 等干扰资产，用于验证 deb 筛选不会误匹配
_ORCA_RELEASE_JSON: str = (
    Path(__file__).parent.joinpath("fixtures", "orca_release_latest.json")
    .read_text(encoding="utf-8")
)

# packages.toml 中 orca-ide 包的生产规则（rule：版本取 tag_name，URL 按 asset 名后缀筛选）
_ORCA_VERSION_RULE: dict[str, Any] = {
    "kind": "jmespath",
    "expr": "tag_name",
    "regex": r"^v(\d+\.\d+\.\d+)$",
    "group": 1,
}
_ORCA_URL_X86_64_RULE: dict[str, Any] = {
    "kind": "jmespath",
    "expr": "assets[?ends_with(name, '_amd64.deb')].browser_download_url | [0]",
}
_ORCA_URL_AARCH64_RULE: dict[str, Any] = {
    "kind": "jmespath",
    "expr": "assets[?ends_with(name, '_arm64.deb')].browser_download_url | [0]",
}


def _zcode_parser() -> RuleDebParser:
    return RuleDebParser(
        _APP_CONFIG,
        url={"x86_64": _ZCODE_URL_X86_64_RULE, "aarch64": _ZCODE_URL_AARCH64_RULE},
    )


def _orca_parser() -> RuleParser:
    return RuleParser(
        _APP_CONFIG,
        version=_ORCA_VERSION_RULE,
        url={"x86_64": _ORCA_URL_X86_64_RULE, "aarch64": _ORCA_URL_AARCH64_RULE},
    )


def _rule(**overrides: Any) -> dict[str, Any]:
    """基础 xpath + 正则变换规则，可按字段覆盖"""
    rule: dict[str, Any] = {
        "kind": "xpath",
        "expr": '//div[@class="note-title"]/b/text()',
        "regex": r"version\s+(\d+\.\d+\.\d+)",
        "group": 1,
    }
    rule.update(overrides)
    return rule


# ── 构造校验：配置错误 fail-fast 抛 ValueError ───────────────────────────────


@pytest.mark.parametrize(
    ("rule", "label"),
    [
        ({"kind": "bogus", "expr": "x"}, "未知 kind"),
        ({"kind": "xpath"}, "缺 expr"),
        ({"kind": "xpath", "expr": ""}, "空 expr"),
        (_rule(regex="("), "非法正则"),
        (_rule(group=-1), "负 group"),
        (_rule(group="1"), "非整数 group"),
        (_rule(group=1, template="{0}"), "group 与 template 同填"),
        (_rule(regex=r"(\d+)\.(\d+)", template="{2}"), "template 占位符越界"),
        (
            {"kind": "xpath", "expr": "//b/text()", "template": "{0}"},
            "template 缺 regex 搭配",
        ),
        (_rule(regex=r"(\d+)\.(\d+)", template="{0}a{x}"), "template 非法占位符"),
        (_rule(regex=r"(\d+)", group=2), "group 超出 regex 捕获组数"),
        (
            {"kind": "re", "expr": r"v(\d+)", "group": 2},
            "re 选择器 group 越界",
        ),
        (_rule(join=1), "非字符串 join"),
        (_rule(first="yes"), "非布尔 first"),
        (_rule(expr="//["), "非法 xpath 表达式"),
        ({"kind": "jmespath", "expr": "info.["}, "非法 jmespath 表达式"),
        ({"kind": "css", "expr": "a["}, "非法 css 表达式"),
    ],
)
def test_invalid_rule_raises(rule: dict[str, Any], label: str) -> None:
    with pytest.raises(ValueError):
        RuleParser(_APP_CONFIG, version=rule)


def test_non_dict_rule_raises() -> None:
    with pytest.raises(ValueError):
        RuleParser(_APP_CONFIG, version=cast(dict[str, Any], "xpath"))


def test_invalid_url_rule_raises() -> None:
    with pytest.raises(ValueError):
        RuleParser(_APP_CONFIG, version=_rule(), url={"x86_64": {"kind": "bogus"}})


# ── parse_version：xpath / css / jmespath / re 四类选择器 ────────────────────


def test_xpath_with_regex_group() -> None:
    parser = RuleParser(_APP_CONFIG, version=_rule())
    assert parser.parse_version(_NAVICAT_HTML) == "17.3.10"


def test_css_selector() -> None:
    rule = _rule(kind="css", expr="div.note-title b::text")
    assert RuleParser(_APP_CONFIG, version=rule).parse_version(_NAVICAT_HTML) == "17.3.10"


def test_jmespath() -> None:
    payload = json.dumps({"info": {"version": "1.2.3"}})
    rule = {"kind": "jmespath", "expr": "info.version"}
    assert RuleParser(_APP_CONFIG, version=rule).parse_version(payload) == "1.2.3"


def test_re_kind_returns_whole_match_by_default() -> None:
    """group=0（默认）返回每个匹配的完整文本，多匹配取首个"""
    rule = {"kind": "re", "expr": r"v(\d+\.\d+)"}
    assert RuleParser(_APP_CONFIG, version=rule).parse_version("a v1.2 b v2.0") == "v1.2"


def test_re_kind_with_group() -> None:
    rule = {"kind": "re", "expr": r"v(\d+\.\d+)", "group": 1}
    assert RuleParser(_APP_CONFIG, version=rule).parse_version("a v1.2 b v2.0") == "1.2"


# ── 变换：template 拼接多捕获组 / 无变换直取 ─────────────────────────────────


def test_template_joins_groups() -> None:
    rule = _rule(regex=r"(\d+)\.(\d+)\.(\d+)", group=0, template="{0}_{1}_{2}")
    assert (
        RuleParser(_APP_CONFIG, version=rule).parse_version(_NAVICAT_HTML) == "17_3_10"
    )


def test_no_transform_returns_selected_text() -> None:
    rule = {"kind": "jmespath", "expr": "info.version"}
    payload = json.dumps({"info": {"version": "1.2.3"}})
    assert RuleParser(_APP_CONFIG, version=rule).parse_version(payload) == "1.2.3"


def test_first_false_joins_all_hits() -> None:
    payload = json.dumps({"items": ["1.0", "2.0"]})
    rule = {"kind": "jmespath", "expr": "items", "first": False, "join": "+"}
    assert RuleParser(_APP_CONFIG, version=rule).parse_version(payload) == "1.0+2.0"


# ── 失败路径：未命中 / 变换无结果 / 非法响应 ─────────────────────────────────


def _structure_changed(caplog: pytest.LogCaptureFixture) -> bool:
    return "疑似上游结构变更" in caplog.text


def test_selector_no_match(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING, logger="aur_metadata.parsers.rule"):
        assert RuleParser(_APP_CONFIG, version=_rule()).parse_version("<p>nothing</p>") is None
    assert _structure_changed(caplog)


def test_regex_no_match(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING, logger="aur_metadata.parsers.rule"):
        assert (
            RuleParser(_APP_CONFIG, version=_rule(regex=r"nomatch(\d+)"))
            .parse_version(_NAVICAT_HTML)
            is None
        )
    assert _structure_changed(caplog)


def test_jmespath_non_str_result(caplog: pytest.LogCaptureFixture) -> None:
    payload = json.dumps({"info": {"version": 12}})
    with caplog.at_level(logging.WARNING, logger="aur_metadata.parsers.rule"):
        assert (
            RuleParser(_APP_CONFIG, version={"kind": "jmespath", "expr": "info.version"})
            .parse_version(payload)
            is None
        )
    assert _structure_changed(caplog)


def test_jmespath_invalid_json() -> None:
    rule = {"kind": "jmespath", "expr": "info.version"}
    assert RuleParser(_APP_CONFIG, version=rule).parse_version("{not json") is None


def test_re_kind_without_match() -> None:
    rule = {"kind": "re", "expr": r"nomatch\d+"}
    assert RuleParser(_APP_CONFIG, version=rule).parse_version("nothing") is None


# ── parse_url：静态直链 / 动态规则 / 缺架构 ──────────────────────────────────


def _static_urls() -> UrlRuleMap:
    return {"x86_64": "https://dn/x.AppImage", "aarch64": "https://dn/a.AppImage"}


def test_parse_url_static_string_rules() -> None:
    parser = RuleParser(_APP_CONFIG, version=_rule(), url=_static_urls())
    # 静态直链与响应无关
    assert parser.parse_url(ArchEnum.X86_64, "") == "https://dn/x.AppImage"
    assert parser.parse_url(ArchEnum.AARCH64, "") == "https://dn/a.AppImage"


def test_parse_url_dynamic_rule() -> None:
    payload = json.dumps(
        {"urls": [{"packagetype": "bdist_wheel", "url": "https://x.whl"},
                  {"packagetype": "sdist", "url": "https://x.tar.gz"}]}
    )
    parser = RuleParser(
        _APP_CONFIG,
        version=_rule(),
        url={"any": {"kind": "jmespath", "expr": "urls[?packagetype=='sdist'] | [0].url"}},
    )
    assert parser.parse_url("any", payload) == "https://x.tar.gz"


def test_parse_url_missing_arch(caplog: pytest.LogCaptureFixture) -> None:
    parser = RuleParser(_APP_CONFIG, version=_rule(), url={"x86_64": "https://dn/x"})
    with caplog.at_level(logging.WARNING, logger="aur_metadata.parsers.rule"):
        assert parser.parse_url("aarch64", "") is None
    # 缺架构属配置错误，走普通警告而非结构变更
    assert "url 规则中无 aarch64 架构" in caplog.text


# ── 跨方法缓存：jmespath 规则 version + url 同一响应只解析一次 ───────────────


def test_jmespath_rules_share_single_parse() -> None:
    payload = json.dumps({"info": {"version": "1.0"}, "url": "https://x/t.gz"})
    parser = RuleParser(
        _APP_CONFIG,
        version={"kind": "jmespath", "expr": "info.version"},
        url={"any": {"kind": "jmespath", "expr": "url"}},
    )
    assert parser.parse_version(payload) == "1.0"
    assert parser.parse_url("any", payload) == "https://x/t.gz"


def test_pure_rule_parser_requires_version_rule() -> None:
    """纯 rule 解析器缺 version 规则属配置错误，构造期抛 ValueError"""
    with pytest.raises(ValueError):
        RuleParser(_APP_CONFIG)


# ── RuleDebParser：URL 规则提取 + deb 头部版本 ───────────────────────────────


def test_rule_deb_parser_version_rule_not_required() -> None:
    """rule-deb 免配 version 规则；文本响应无版本可解析（恒 None）"""
    parser = RuleDebParser(
        _APP_CONFIG, url={"x86_64": {"kind": "jmespath", "expr": "u"}}
    )
    assert parser.parse_version(json.dumps({"u": "https://x/a.deb"})) is None
    assert parser.parse_url("x86_64", json.dumps({"u": "https://x/a.deb"})) == (
        "https://x/a.deb"
    )


def test_rule_deb_parser_version_from_package_head() -> None:
    """版本经 DebControlVersionMixin 从 deb 头部提取并归一化"""
    parser = RuleDebParser(_APP_CONFIG)
    assert (
        parser.version_from_package_head(build_deb(version="3.14.0-7681"))
        == "3.14.0_7681"
    )

# ── ZCode 生产规则（packages.toml，rule-deb）：官网直链文件名锚定 ─────────────


def test_zcode_url_rules_extract_both_archs() -> None:
    """两架构 URL 各自按文件名锚点提取，互不干扰；文本响应无版本（deb 头部提取）"""
    parser = _zcode_parser()
    assert parser.parse_version(_ZCODE_HTML) is None
    assert parser.parse_url(ArchEnum.X86_64, _ZCODE_HTML) == (
        "https://cdn-zcode.z.ai/zcode/electron/releases/3.14.0/linux-x64/"
        "ZCode-3.14.0-linux-x64.deb"
    )
    assert parser.parse_url(ArchEnum.AARCH64, _ZCODE_HTML) == (
        "https://cdn-zcode.z.ai/zcode/electron/releases/3.14.0/linux-arm64/"
        "ZCode-3.14.0-linux-arm64.deb"
    )


def test_zcode_url_rule_fails_on_renamed_artifact() -> None:
    """上游改名（文件名失配）时走结构变更告警返回 None，而非提取错值；
    失配只影响对应架构，另一架构定位不受牵连"""
    html = _ZCODE_HTML.replace("ZCode-3.14.0-linux-x64.deb", "zcode_3.14.0_amd64.deb")
    parser = _zcode_parser()
    assert parser.parse_url(ArchEnum.X86_64, html) is None
    assert parser.parse_url(ArchEnum.AARCH64, html) == (
        "https://cdn-zcode.z.ai/zcode/electron/releases/3.14.0/linux-arm64/"
        "ZCode-3.14.0-linux-arm64.deb"
    )


def test_zcode_version_from_package_head() -> None:
    """版本经 DebControlVersionMixin 从 deb 头部提取并归一化（build 号转 _ 连接）"""
    parser = _zcode_parser()
    assert (
        parser.version_from_package_head(build_deb(version="3.14.0-7681"))
        == "3.14.0_7681"
    )


# ── Orca IDE 生产规则（packages.toml，rule）：GitHub Releases API ─────────────


def test_orca_version_strips_tag_prefix() -> None:
    """tag_name 带 v 前缀，正则单独取出三段式版本号（下游 pkgver 不接受 v）"""
    assert _orca_parser().parse_version(_ORCA_RELEASE_JSON) == "1.4.257"


def test_orca_url_rules_pick_deb_over_lookalike_assets() -> None:
    """按 _amd64.deb / _arm64.deb 后缀筛选，避开 rpm、AppImage 与
    orca-server-linux-*.tar.gz（后两者也带架构标识，前缀匹配会误中）"""
    parser = _orca_parser()
    assert parser.parse_url(ArchEnum.X86_64, _ORCA_RELEASE_JSON) == (
        "https://github.com/stablyai/orca/releases/download/v1.4.257/"
        "orca-ide_1.4.257_amd64.deb"
    )
    assert parser.parse_url(ArchEnum.AARCH64, _ORCA_RELEASE_JSON) == (
        "https://github.com/stablyai/orca/releases/download/v1.4.257/"
        "orca-ide_1.4.257_arm64.deb"
    )


def test_orca_version_regex_rejects_malformed_tag() -> None:
    """tag 不符合 vX.Y.Z 时返回 None 并记结构变更，而非把错误值写进 pkgver"""
    parser = _orca_parser()
    assert parser.parse_version(json.dumps({"tag_name": "nightly-20261112"})) is None


def test_orca_url_rule_returns_none_when_asset_missing() -> None:
    """上游停止发布某架构 deb 时该架构返回 None（走结构变更告警）"""
    payload: dict[str, Any] = {
        "tag_name": "v1.4.258",
        "assets": [
            {
                "name": "orca-ide_1.4.258_amd64.deb",
                "browser_download_url": "https://example.invalid/amd64.deb",
            }
        ],
    }
    parser = _orca_parser()
    assert parser.parse_url(ArchEnum.X86_64, json.dumps(payload)) == (
        "https://example.invalid/amd64.deb"
    )
    assert parser.parse_url(ArchEnum.AARCH64, json.dumps(payload)) is None


# ── 规则链 fallback ──────────────────────────────────────────────────────────


def test_rule_chain_falls_back_to_next_rule() -> None:
    """首条规则失配时由下一条接管，两条都命中时以声明顺序为准"""
    parser = RuleParser(
        _APP_CONFIG,
        version=[
            {"kind": "re", "expr": r"id=(\d+)", "group": 1},
            {"kind": "re", "expr": r"tag=v?(\d+\.\d+\.\d+)", "group": 1},
        ],
    )
    assert parser.parse_version("tag=v2.1.0") == "2.1.0"
    assert parser.parse_version("id=42 tag=v2.1.0") == "42"


def test_rule_chain_reports_only_when_all_rules_miss(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """中间规则失配属预期 fallback，不应产生结构变更告警淹没有效信号"""
    parser = RuleParser(
        _APP_CONFIG,
        version=[
            {"kind": "re", "expr": r"id=(\d+)", "group": 1},
            {"kind": "re", "expr": r"tag=v?(\d+\.\d+\.\d+)", "group": 1},
        ],
    )
    with caplog.at_level(logging.WARNING):
        assert parser.parse_version("tag=v2.1.0") == "2.1.0"
    assert caplog.records == []


def test_rule_chain_rejects_empty_list() -> None:
    with pytest.raises(ValueError, match="不得为空"):
        RuleParser(_APP_CONFIG, version=[])


# ── Zen Browser 生产规则（packages.toml，rule + 规则链） ─────────────────────

_ZEN_RELEASE_JSON: str = (
    Path(__file__).parent.joinpath("fixtures", "zen_release_twilight.json")
    .read_text(encoding="utf-8")
)

_ZEN_VERSION_RULES: list[dict[str, Any]] = [
    {
        "kind": "jmespath",
        "expr": "name",
        "regex": r"(\d+\.\d+[a-z]?)\s*\((\d{4})-(\d{2})-(\d{2})",
        "template": "{0}.{1}{2}{3}",
    },
    {"kind": "jmespath", "expr": "name", "regex": r"\d+\.\d+[a-z]?"},
]


def _zen_parser() -> RuleParser:
    return RuleParser(
        _APP_CONFIG,
        version=_ZEN_VERSION_RULES,
        url={
            "x86_64": {
                "kind": "jmespath",
                "expr": "assets[?name=='zen.linux-x86_64.tar.xz'].browser_download_url | [0]",
            },
            "aarch64": {
                "kind": "jmespath",
                "expr": "assets[?name=='zen.linux-aarch64.tar.xz'].browser_download_url | [0]",
            },
        },
    )


def test_zen_version_joins_date_suffix() -> None:
    """release name 带日期时，版本片段拼上去连字符的日期"""
    assert _zen_parser().parse_version(_ZEN_RELEASE_JSON) == "1.25t.20261111"


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Twilight build - 1.5a", "1.5a"),
        ("Twilight build - 2.0", "2.0"),
    ],
)
def test_zen_version_falls_back_without_date(name: str, expected: str) -> None:
    """name 无日期后缀时由第二条规则取纯版本号，不留分隔符残留"""
    parser = _zen_parser()
    assert parser.parse_version(json.dumps({"name": name})) == expected


def test_zen_url_rules_target_linux_tarballs() -> None:
    """按精确 asset 名取链接，避开同 release 的 AppImage / .mar / 其他平台产物"""
    parser = _zen_parser()
    assert parser.parse_url(ArchEnum.X86_64, _ZEN_RELEASE_JSON) == (
        "https://github.com/zen-browser/desktop/releases/download/twilight-1/"
        "zen.linux-x86_64.tar.xz"
    )
    assert parser.parse_url(ArchEnum.AARCH64, _ZEN_RELEASE_JSON) == (
        "https://github.com/zen-browser/desktop/releases/download/twilight-1/"
        "zen.linux-aarch64.tar.xz"
    )


def test_zen_missing_name_returns_none() -> None:
    assert _zen_parser().parse_version(json.dumps({"assets": []})) is None
