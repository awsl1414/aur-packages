"""解析器类型注册表：parser_type 字符串 → BaseParser 实例的工厂。

新增 parser 时在此注册即可，调度器/注册表加载器通过 ``get_parser`` 按名取实例。
"""

from app.parsers.base import BaseParser
from app.parsers.qq import QQParser

# parser_type → 解析器类；parser 无状态，每次取用 new 一个实例
_PARSER_REGISTRY: dict[str, type[BaseParser]] = {
    "qq": QQParser,
}


def get_parser(parser_type: str) -> BaseParser:
    """按 parser_type 取一个新的解析器实例；未知类型抛 ValueError"""
    cls: type[BaseParser] | None = _PARSER_REGISTRY.get(parser_type)
    if cls is None:
        raise ValueError(f"未知的 parser_type: {parser_type}")
    return cls()


def register_parser(parser_type: str, cls: type[BaseParser]) -> None:
    """注册一个解析器类型（供扩展/测试注入）"""
    _PARSER_REGISTRY[parser_type] = cls
