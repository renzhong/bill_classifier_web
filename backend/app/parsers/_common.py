"""字段定位与解析通用工具：所有 parser 共用"""
from __future__ import annotations

import csv
import io
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

import chardet

_AMOUNT_STRIP = re.compile(r"[¥￥,，\s]")
_TIME_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y-%m-%d %H:%M")


def detect_decode(data: bytes, prefer: str) -> str:
    """优先用 prefer 编码解码；失败时用 chardet 兜底"""
    try:
        data.decode(prefer)
        return prefer
    except UnicodeDecodeError:
        guess = chardet.detect(data[:65536]) or {}
        enc = (guess.get("encoding") or "utf-8").lower()
        return enc


def read_rows(data: bytes, prefer_encoding: str) -> list[list[str]]:
    enc = detect_decode(data, prefer_encoding)
    text = data.decode(enc, errors="replace")
    reader = csv.reader(io.StringIO(text))
    return [[c.strip() for c in row] for row in reader if row]


def find_header_row(rows: list[list[str]], must_have: list[str]) -> int:
    """返回表头行索引；按"必须包含这些列名"判断"""
    for i, row in enumerate(rows):
        joined = "".join(row)
        if all(name in joined for name in must_have):
            return i
    raise ValueError(f"header row not found, expected columns: {must_have}")


def parse_amount(text: str) -> Decimal:
    cleaned = _AMOUNT_STRIP.sub("", text or "")
    if not cleaned:
        raise ValueError("empty amount")
    try:
        return Decimal(cleaned).quantize(Decimal("0.01"))
    except InvalidOperation as e:
        raise ValueError(f"bad amount: {text!r}") from e


def parse_time(text: str) -> datetime:
    text = (text or "").strip()
    for fmt in _TIME_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError(f"bad time format: {text!r}")


def normalize_bill_type(text: str | None) -> str:
    s = (text or "").strip()
    if s.startswith("收"):
        return "income"
    if s.startswith("支"):
        return "expense"
    # 支付宝："不计收支"，微信："不计支出"，统一 other
    if "不计" in s or s in ("/", "中性", ""):
        return "other"
    return "other"


def get_col(row: list[str], idx: int | None) -> str:
    if idx is None or idx >= len(row):
        return ""
    return row[idx].strip()


def index_map(header: list[str]) -> dict[str, int]:
    """规整 header 名称（去除空格 / 全角括号）→ index"""
    out: dict[str, int] = {}
    for i, name in enumerate(header):
        key = name.replace(" ", "").replace("（", "(").replace("）", ")")
        out[key] = i
    return out
