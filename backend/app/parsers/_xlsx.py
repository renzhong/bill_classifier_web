"""xlsx → list[list[str]]：把 Excel sheet 拍平成与 csv 同形态的二维字符串

只读首个 sheet，使用 read_only + data_only 避免大文件内存爆炸。
日期单元格统一格式化成 '%Y-%m-%d %H:%M:%S'，与 _common.parse_time 兼容。
"""
from __future__ import annotations

from datetime import date, datetime, time
from io import BytesIO

from openpyxl import load_workbook


def xlsx_to_rows(data: bytes) -> list[list[str]]:
    wb = load_workbook(BytesIO(data), read_only=True, data_only=True)
    try:
        ws = wb[wb.sheetnames[0]]
        rows: list[list[str]] = []
        for row in ws.iter_rows(values_only=True):
            rows.append([_cell_to_str(c) for c in row])
        return rows
    finally:
        wb.close()


def _cell_to_str(val: object) -> str:
    if val is None:
        return ""
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(val, date):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, time):
        return val.strftime("%H:%M:%S")
    return str(val).strip()
