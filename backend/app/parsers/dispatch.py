"""上传文件分发：识别 csv / xlsx 后路由到 declared_source 对应的 parser"""
from __future__ import annotations

import codecs
from typing import Literal

from app.parsers import get_parser
from app.parsers._xlsx import xlsx_to_rows
from app.parsers.base import ParseError, ParseResult

FileKind = Literal["xlsx", "csv", "unknown"]

_ZIP_MAGIC = b"PK\x03\x04"


def sniff(data: bytes, filename: str) -> FileKind:
    name = (filename or "").lower()
    if data.startswith(_ZIP_MAGIC) and name.endswith(".xlsx"):
        return "xlsx"
    if data.startswith(_ZIP_MAGIC):
        # zip 或 office 老格式：不支持
        return "unknown"
    # 尝试文本解码（utf-8 优先，gbk 兜底）
    probe = data[:4096]
    for enc in ("utf-8", "utf-8-sig", "gbk"):
        try:
            # The probe can end in the middle of a valid multibyte character.
            codecs.getincrementaldecoder(enc)().decode(probe, final=len(data) <= len(probe))
            return "csv"
        except UnicodeDecodeError:
            continue
    return "unknown"


def parse_upload(
    data: bytes,
    filename: str,
    declared_source: str,
    owner: str | None = None,
) -> ParseResult:
    kind = sniff(data, filename)
    if kind == "unknown":
        raise ParseError("不支持的文件格式，请上传 .csv 或 .xlsx")

    parser = get_parser(declared_source)

    if kind == "xlsx":
        rows = xlsx_to_rows(data)
        return parser.parse_rows(rows, owner=owner)  # type: ignore[attr-defined]

    return parser.parse(data, owner=owner)
