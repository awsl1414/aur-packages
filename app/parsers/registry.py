"""解析器类型注册表：parser_type 字符串 → BaseParser 实例的工厂。

新增 parser 时在此注册即可，调度器/注册表加载器通过 ``get_parser`` 按名取实例。
parser 的构造参数（如 TraeParser 的 region、NavicatParser 的 urls）由
``packages.parser_config``（JSON）注入，``get_parser`` 用 ``cls(**config)`` 实例化。
"""

from typing import Any

from app.parsers.base import BaseParser
from app.parsers.deb import DebParser
from app.parsers.navicat import NavicatParser
from app.parsers.pypi import PyPIParser
from app.parsers.qq import QQParser
from app.parsers.trae import TraeParser
from app.parsers.zen import ZenParser

# parser_type → 解析器类。parser 实例仅持有上一响应的解析缓存
# （见 BaseParser._parse_json_dict），无其他跨请求状态
_PARSER_REGISTRY: dict[str, type[BaseParser]] = {
    "qq": QQParser,
    "navicat": NavicatParser,
    "pypi": PyPIParser,
    "trae": TraeParser,
    "zen": ZenParser,
    "deb": DebParser,
}


def get_parser(parser_type: str, config: dict[str, Any] | None = None) -> BaseParser:
    """按 parser_type 取一个新的解析器实例；未知类型抛 ValueError。

    ``config`` 为该 parser 的构造参数（源自 ``packages.parser_config``），
    以 ``cls(**config)`` 透传给 ``__init__``；为空则无参构造。
    """
    cls: type[BaseParser] | None = _PARSER_REGISTRY.get(parser_type)
    if cls is None:
        raise ValueError(f"未知的 parser_type: {parser_type}")
    return cls(**config) if config else cls()


def get_parser_types() -> list[str]:
    """返回所有已注册的 parser_type（供包配置校验使用）"""
    return list(_PARSER_REGISTRY)


def register_parser(parser_type: str, cls: type[BaseParser]) -> None:
    """注册一个解析器类型（供扩展/测试注入）"""
    _PARSER_REGISTRY[parser_type] = cls
