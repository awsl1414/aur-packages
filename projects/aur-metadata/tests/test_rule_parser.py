"""aur_metadata.parsers.rule 单元测试"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, cast

import pytest

from aur_metadata.constants import ArchEnum
from aur_metadata.parsers.rule import RuleDebParser, RuleParser
from tests.fakes import build_deb, make_app_config

_APP_CONFIG = make_app_config()

# 真实 Navicat release-note 页面片段（含 platform="L" 表与 note-title 结构）
_NAVICAT_HTML: str = (
    Path(__file__).parent.joinpath("fixtures", "navicat_release_note.html")
    .read_text(encoding="utf-8")
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


def _static_urls() -> dict[str, dict[str, Any] | str]:
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
