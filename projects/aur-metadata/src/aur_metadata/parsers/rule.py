"""通用规则化解析器：parser_type ``"rule"``。

面向「单次定位 + 一次变换」即可完成提取的简单数据源（HTML 页面 / JSON API），
用声明式规则替代专属 parser 类——新增此类上游只改 packages.toml，不写代码。

规则模型（两段式，全部字段可 JSON 序列化，经 packages.parser_config 落库）：

- 选择器（必填）：``kind`` + ``expr``
  - ``xpath`` / ``css``：HTML/XML 文档（parsel Selector）
  - ``jmespath``：JSON 文档（复用基类 ``_parse_json_dict`` 的按响应缓存）
  - ``re``：对原始响应文本直接正则
  - 命中多个结果时默认取首个（``first``），``first=false`` 则以 ``join``
    分隔符拼接全部命中
- 变换（可选）：对选择结果应用 ``regex``，取捕获组 ``group`` 或按
  ``template``（如 ``"{0}.{1}"``）拼接多个捕获组

配置形态::

    version = { kind = "xpath", expr = "...", regex = "...", group = 1 }
    url.x86_64 = "https://static/direct-link"          # 静态直链
    url."any" = { kind = "jmespath", expr = "..." }     # 动态提取

版本来自 deb 安装包头部（响应无版本字段）时使用 ``parser_type = "rule-deb"``
（``RuleDebParser``）：免配 version 规则，URL 仍按上述规则提取，版本由服务层
下载头部后统一提取。

能力边界（需求命中任一条即应写专属 parser）：不支持多规则 fallback、
鉴权/签名下载、跨字段或跨架构一致性校验、二进制内容提取、条件分支逻辑。

配置错误（未知 kind、非法正则、group 与 template 同填等）构造时抛
``ValueError`` fail-fast；上游结构变更（选择器未命中、变换无结果等）走
``_log_structure_change`` 返回 None。
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

import jmespath
from parsel import Selector

from aur_metadata.config import AppConfig
from aur_metadata.constants import ArchEnum

from .base import BaseParser
from .deb import DebControlVersionMixin

logger = logging.getLogger(__name__)

# 支持的选择器类型
_RULE_KINDS: frozenset[str] = frozenset({"xpath", "css", "jmespath", "re"})


@dataclass(frozen=True)
class ExtractRule:
    """单条提取规则：选择器（kind + expr）+ 可选变换（regex → group/template）"""

    kind: str
    expr: str
    first: bool = True
    join: str = ""
    regex: str | None = None
    group: int = 0
    template: str | None = None
    # regex 编译产物（frozen dataclass 经 __post_init__ 写入）
    _compiled: re.Pattern[str] | None = field(
        default=None, init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        compiled: re.Pattern[str] | None = (
            re.compile(self.regex) if self.regex is not None else None
        )
        object.__setattr__(self, "_compiled", compiled)
        if self.template is None:
            if compiled is not None and self.group > compiled.groups:
                # group 越界会在运行期才爆 IndexError，构造期拦下
                raise ValueError(
                    f"group {self.group} 超出 regex 捕获组数 ({compiled.groups})"
                )
            return
        if compiled is None:
            # 无 regex 时 template 永不生效，静默忽略会掩盖配置错误
            raise ValueError("template 须与 regex 搭配使用")
        try:
            # 干跑 format：占位符越界（IndexError）或非法（KeyError）构造期拦下
            self.template.format(*([""] * compiled.groups))
        except (IndexError, KeyError, ValueError) as e:
            raise ValueError(f"template 与 regex 捕获组数不匹配: {e}") from e


def _build_rule(data: Any, label: str) -> ExtractRule:
    """构造并校验单条规则；配置错误抛 ValueError（构造期 fail-fast）。"""
    if not isinstance(data, dict):
        raise ValueError(f"rule.{label} 必须为表（table）")
    kind: Any = data.get("kind")
    if not isinstance(kind, str) or kind not in _RULE_KINDS:
        raise ValueError(
            f"rule.{label}.kind 必须为 {_sorted_kinds()} 之一，得到 {kind!r}"
        )
    expr: Any = data.get("expr")
    if not isinstance(expr, str) or not expr:
        raise ValueError(f"rule.{label}.expr 必须为非空字符串")

    regex: Any = data.get("regex")
    group: Any = data.get("group", 0)
    template: Any = data.get("template")
    if regex is not None and (not isinstance(regex, str) or not regex):
        raise ValueError(f"rule.{label}.regex 置非空时必须为非空字符串")
    if not isinstance(group, int) or isinstance(group, bool) or group < 0:
        raise ValueError(f"rule.{label}.group 必须为非负整数")
    if template is not None and (not isinstance(template, str) or not template):
        raise ValueError(f"rule.{label}.template 置非空时必须为非空字符串")
    if template is not None and group != 0:
        raise ValueError(f"rule.{label}: group 与 template 不可同填")
    join: Any = data.get("join", "")
    if not isinstance(join, str):
        raise ValueError(f"rule.{label}.join 必须为字符串")
    first: Any = data.get("first", True)
    if not isinstance(first, bool):
        raise ValueError(f"rule.{label}.first 必须为布尔值")

    try:
        rule = ExtractRule(
            kind=kind,
            expr=expr,
            first=first,
            join=join,
            regex=regex,
            group=group,
            template=template,
        )
    except re.error as e:
        raise ValueError(f"rule.{label}.regex 非法: {e}") from e
    _validate_expr_syntax(kind, expr, label, group=group)
    return rule


def _validate_expr_syntax(
    kind: str, expr: str, label: str, *, group: int = 0
) -> None:
    """kind 专属表达式语法校验，构造期拦下配置错误（fail-fast）。

    xpath/css 借 parsel 对空文档求值触发 lxml/cssselect 的语法检查；
    jmespath/re 直接编译。``group`` 仅对 kind=re 有意义（选择器自身的
    捕获组序号），须不超出 expr 的捕获组数。表达式语义（能否命中目标）
    不在此列——那属上游结构变更，运行期走 _log_structure_change。
    """
    try:
        if kind == "re":
            pattern: re.Pattern[str] = re.compile(expr)
            if group > pattern.groups:
                raise ValueError(
                    f"group {group} 超出表达式捕获组数 ({pattern.groups})"
                )
        elif kind == "jmespath":
            jmespath.compile(expr)
        elif kind == "xpath":
            Selector(text="<p/>").xpath(expr)
        else:  # css
            Selector(text="<p/>").css(expr)
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"rule.{label} 的 {kind} 表达式语法错误: {e}") from e


def _sorted_kinds() -> str:
    return "/".join(sorted(_RULE_KINDS))


class RuleParser(BaseParser):
    """规则化解析器：version/url 均由声明式规则驱动。

    构造参数（packages.parser_config）：

    - ``version``：版本提取规则（dict）；纯 rule 解析器必填（缺失构造期
      抛 ValueError），``RuleDebParser`` 版本来自安装包头部，不适用
    - ``url``：arch_value → 规则 dict 或静态 URL 字符串（缺架构的
      parse_url 返回 None，属配置错误走普通日志）
    """

    # 版本规则是否必填：deb 变体（RuleDebParser）版本来自安装包头部提取
    _version_required: bool = True

    def __init__(
        self,
        app_config: AppConfig,
        version: dict[str, Any] | None = None,
        url: dict[str, dict[str, Any] | str] | None = None,
    ) -> None:
        super().__init__(app_config)
        if version is None and self._version_required:
            raise ValueError("rule 解析器必须配置 version 版本提取规则")
        self._version_rule: ExtractRule | None = (
            _build_rule(version, "version") if version is not None else None
        )
        self._url_rules: dict[str, ExtractRule | str] = {
            arch: url_value if isinstance(url_value, str) else _build_rule(
                url_value, f"url.{arch}"
            )
            for arch, url_value in (url or {}).items()
        }

    def parse_version(self, response_data: str) -> str | None:
        if self._version_rule is None:
            return None
        return self._extract(self._version_rule, response_data, context="version")

    def parse_url(self, arch: ArchEnum | str, response_data: str) -> str | None:
        arch_value: str = self._arch_value(arch)
        rule: ExtractRule | str | None = self._url_rules.get(arch_value)
        if rule is None:
            # 缺规则属包配置错误而非上游变更，走普通日志
            logger.warning("RuleParser: url 规则中无 %s 架构", arch_value)
            return None
        if isinstance(rule, str):
            return rule
        return self._extract(rule, response_data, context=f"url({arch_value})")

    def _extract(self, rule: ExtractRule, response_data: str, context: str) -> str | None:
        """选择 → 合并 → 变换三段提取；无命中/无变换结果记结构变更返回 None。"""
        texts: list[str] | None = self._select(rule, response_data)
        if texts is None:
            return None
        text: str = texts[0] if rule.first else rule.join.join(texts)

        if rule._compiled is None:
            return text
        match: re.Match[str] | None = rule._compiled.search(text)
        if match is None:
            self._log_structure_change(
                f"{context}: 变换正则未命中", text or response_data
            )
            return None
        if rule.template is not None:
            return rule.template.format(*match.groups())
        return match.group(rule.group)

    def _select(self, rule: ExtractRule, response_data: str) -> list[str] | None:
        """按 kind 执行选择，返回命中的文本列表；无命中返回 None。"""
        if rule.kind == "re":
            texts: list[str] = [
                match.group(rule.group)
                for match in re.finditer(rule.expr, response_data)
            ]
        elif rule.kind == "jmespath":
            data: dict[str, Any] | None = self._parse_json_dict(response_data)
            if data is None:
                return None
            result: Any = jmespath.search(rule.expr, data)
            if isinstance(result, str):
                texts = [result]
            elif isinstance(result, list) and all(isinstance(t, str) for t in result):
                texts = result
            else:
                self._log_structure_change(
                    f"{rule.kind} 选择结果非字符串: {result!r}", response_data
                )
                return None
        else:
            selector: Selector = Selector(text=response_data)
            method = selector.xpath if rule.kind == "xpath" else selector.css
            texts = method(rule.expr).getall()
        if not texts:
            self._log_structure_change(
                f"{rule.kind} 选择器未命中: {rule.expr}", response_data
            )
            return None
        return texts


class RuleDebParser(DebControlVersionMixin, RuleParser):
    """rule 解析器的 deb 变体（parser_type ``"rule-deb"``）。

    补齐「URL 从响应规则提取 + 版本从 deb 头部权威提取」组合：各架构安装包
    URL 由 ``url`` 规则定位（动态，无静态配置），版本由服务层下载安装包头部
    后经 ``version_from_package_head`` 提取——版本源响应无版本字段亦可。
    需要额外下载处理（签名等）时继承本类重写 ``resolve_raw_url``，
    鉴权逻辑不进规则引擎。
    """

    _version_required = False
