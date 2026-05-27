from app.parsers.alipay import AlipayParser
from app.parsers.base import BillItem, ParseError, Parser
from app.parsers.wechat import WechatParser

PARSER_REGISTRY: dict[str, type[Parser]] = {
    "alipay": AlipayParser,
    "wechat": WechatParser,
}


def get_parser(source: str) -> Parser:
    cls = PARSER_REGISTRY.get(source)
    if not cls:
        raise ParseError(f"unsupported source: {source}")
    return cls()


__all__ = ["BillItem", "ParseError", "Parser", "AlipayParser", "WechatParser", "get_parser", "PARSER_REGISTRY"]
