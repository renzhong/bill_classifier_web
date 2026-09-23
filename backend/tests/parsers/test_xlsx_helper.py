"""xlsx_to_rows：内存里写一个 workbook，验证 cell → str 的转换规则"""
from __future__ import annotations

from datetime import date, datetime
from io import BytesIO

from openpyxl import Workbook

from app.parsers._xlsx import xlsx_to_rows


def _make_xlsx(rows: list[list[object]]) -> bytes:
    wb = Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_string_int_float_none():
    data = _make_xlsx([
        ["a", 1, 2.5, None, ""],
    ])
    rows = xlsx_to_rows(data)
    assert rows == [["a", "1", "2.5", "", ""]]


def test_datetime_formatting():
    # openpyxl read_only 模式下 date/time 单元格都会被读成 datetime
    data = _make_xlsx([
        ["t1", datetime(2026, 5, 31, 19, 56, 10)],
        ["t2", date(2026, 1, 5)],
    ])
    rows = xlsx_to_rows(data)
    assert rows[0][1] == "2026-05-31 19:56:10"
    assert rows[1][1].startswith("2026-01-05")


def test_trailing_whitespace_stripped():
    data = _make_xlsx([["  hello  "]])
    rows = xlsx_to_rows(data)
    assert rows[0][0] == "hello"
