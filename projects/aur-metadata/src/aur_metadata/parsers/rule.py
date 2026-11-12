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
  ``template``（如 ``"{0}.{1}"``）拼接多个捕获组。template 引用的组必须全部
  命中，否则该规则判为失配——部分缺失时拼出的残缺值（如 ``"1.2."``）看着
  合法却错误，比直接 fallback 更难发现
- 规则链（可选）：``version`` / ``url.<arch>`` 可写成规则表列表，按声明顺序
  尝试，首个提取到值的规则生效。用于上游存在多种可选形态的数据源，只有末条
  规则失配才记结构变更告警

配置形态::

    version = { kind = "xpath", expr = "...", regex = "...", group = 1 }
    version = [{ ... 带日期形态 ... }, { ... 无日期形态 ... }]   # fallback 链
    url.x86_64 = "https://static/direct-link"          # 静态直链
    url."any" = { kind = "jmespath", expr = "..." }     # 动态提取

版本来自 deb 安装包头部（响应无版本字段）时使用 ``parser_type = "rule-deb"``
（``RuleDebParser``）：免配 version 规则，URL 仍按上述规则提取，版本由服务层
下载头部后统一提取。

能力边界（需求命中任一条即应写专属 parser）：鉴权/签名下载、跨字段或跨架构
一致性校验（如 trae 要求各架构版本一致）、二进制内容提取、条件分支逻辑。

配置错误（未知 kind、非法正则、group 与 template 同填等）构造时抛
``ValueError`` fail-fast；上游结构变更（选择器未命中、变换无结果等）走
``_log_structure_change`` 返回 None。
"""


import logging
import re
from dataclasses import dataclass, field
from string import Formatter
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
    # template 实际引用的捕获组索引，运行期据此判断是否有组未命中
    _template_groups: tuple[int, ...] = field(
        default=(), init=False, repr=False, compare=False
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
            # 干跑 format：占位符越界（IndexError）、非整数键（KeyError）、
            # 属性/下标访问（AttributeError/TypeError）构造期一并拦下
            self.template.format(*([""] * compiled.groups))
        except (IndexError, KeyError, ValueError, AttributeError, TypeError) as e:
            raise ValueError(f"template 与 regex 捕获组数不匹配: {e}") from e
        # 仅记录 template 真正引用的组：未引用的组缺失不影响输出。
        # 非整数占位符（{name}、{0.x}）已在上面的干跑中拦下，此处可安全转 int
        groups: tuple[int, ...] = tuple(
            int(index)
            for _, index, _, _ in Formatter().parse(self.template)
            if index is not None
        )
        object.__setattr__(self, "_template_groups", groups)


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


def _build_rules(data: Any, label: str) -> list[ExtractRule]:
    """构造规则链：接受单条规则表或规则表列表，按声明顺序依次尝试。

    列表语义是 fallback——任一规则提取到值即返回，用于上游存在多种可选
    形态的场景（如 release name 有/无日期后缀）。空列表视为配置错误。
    """
    if isinstance(data, list):
        if not data:
            raise ValueError(f"rule.{label} 规则列表不得为空")
        return [
            _build_rule(item, f"{label}[{index}]")
            for index, item in enumerate(data)
        ]
    return [_build_rule(data, label)]


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


# 规则声明：单条规则表，或按顺序 fallback 的规则表列表
RuleSpec = dict[str, Any]
RuleChain = RuleSpec | list[RuleSpec]
# arch → 规则链 / 静态 URL
UrlRuleMap = dict[str, RuleChain | str]


class RuleParser(BaseParser):
    """规则化解析器：version/url 均由声明式规则驱动。

    构造参数（packages.parser_config）：

    - ``version``：版本提取规则（dict 或 dict 列表）；纯 rule 解析器必填
      （缺失构造期抛 ValueError），``RuleDebParser`` 版本来自安装包头部，不适用
    - ``url``：arch_value → 规则 dict / 规则 dict 列表 / 静态 URL 字符串
      （缺架构的 parse_url 返回 None，属配置错误走普通日志）

    规则列表为 fallback 语义：按声明顺序尝试，首个提取到值的规则生效。
    """

    # 版本规则是否必填：deb 变体（RuleDebParser）版本来自安装包头部提取
    _version_required: bool = True

    def __init__(
        self,
        app_config: AppConfig,
        version: RuleChain | None = None,
        url: UrlRuleMap | None = None,
    ) -> None:
        super().__init__(app_config)
        if version is None and self._version_required:
            raise ValueError("rule 解析器必须配置 version 版本提取规则")
        self._version_rules: list[ExtractRule] = (
            _build_rules(version, "version") if version is not None else []
        )
        self._url_rules: dict[str, list[ExtractRule] | str] = {
            arch: url_value if isinstance(url_value, str) else _build_rules(
                url_value, f"url.{arch}"
            )
            for arch, url_value in (url or {}).items()
        }

    def parse_version(self, response_data: str) -> str | None:
        return self._extract_first(self._version_rules, response_data, context="version")

    def parse_url(self, arch: ArchEnum | str, response_data: str) -> str | None:
        arch_value: str = self._arch_value(arch)
        rules: list[ExtractRule] | str | None = self._url_rules.get(arch_value)
        if rules is None:
            # 缺规则属包配置错误而非上游变更，走普通日志
            logger.warning("RuleParser: url 规则中无 %s 架构", arch_value)
            return None
        if isinstance(rules, str):
            return rules
        return self._extract_first(rules, response_data, context=f"url({arch_value})")

    def _extract_first(
        self, rules: list[ExtractRule], response_data: str, context: str
    ) -> str | None:
        """按顺序尝试规则链，返回首个提取结果；全部未命中返回 None。

        只有最后一条规则失配时才记结构变更日志——前面的规则是允许失配的
        fallback 分支，逐条告警会淹没真正的问题。
        """
        if not rules:
            return None
        for rule in rules[:-1]:
            result: str | None = self._extract(
                rule, response_data, context=context, quiet=True
            )
            if result is not None:
                return result
        return self._extract(rules[-1], response_data, context=context)

    def _extract(
        self,
        rule: ExtractRule,
        response_data: str,
        context: str,
        *,
        quiet: bool = False,
    ) -> str | None:
        """选择 → 合并 → 变换三段提取；无命中/无变换结果记结构变更返回 None。

        ``quiet`` 用于规则链的非末位规则：失配属预期 fallback，不记结构变更
        告警，避免多形态上游每轮采集都刷出误报。
        """
        texts: list[str] | None = self._select(rule, response_data, quiet=quiet)
        if texts is None:
            return None
        text: str = texts[0] if rule.first else rule.join.join(texts)

        if rule._compiled is None:
            return text
        match: re.Match[str] | None = rule._compiled.search(text)
        if match is None:
            if not quiet:
                self._log_structure_change(
                    f"{context}: 变换正则未命中", text or response_data
                )
            return None
        if rule.template is not None:
            # template 引用的捕获组必须全部命中。部分缺失时若按空串代入，
            # "1.2." 这类看着合法的残缺版本号会被写进 pkgver，下游无从发现；
            # 判为失配让规则链 fallback 到能表达该形态的下一条规则
            groups: tuple[str | None, ...] = match.groups()
            missing: list[int] = [
                index
                for index in rule._template_groups
                if index >= len(groups) or groups[index] is None
            ]
            if missing:
                if not quiet:
                    self._log_structure_change(
                        f"{context}: template 引用的捕获组未命中 {missing}",
                        text or response_data,
                    )
                return None
            return rule.template.format(*groups)
        return match.group(rule.group)

    def _select(
        self, rule: ExtractRule, response_data: str, *, quiet: bool = False
    ) -> list[str] | None:
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
                if not quiet:
                    self._log_structure_change(
                        f"{rule.kind} 选择结果非字符串: {result!r}", response_data
                    )
                return None
        else:
            selector: Selector = Selector(text=response_data)
            method = selector.xpath if rule.kind == "xpath" else selector.css
            texts = method(rule.expr).getall()
        if not texts:
            if not quiet:
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
