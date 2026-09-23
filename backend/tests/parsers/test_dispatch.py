"""sniff + parse_upload 的分支覆盖"""
from __future__ import annotations

from io import BytesIO

import pytest
from openpyxl import Workbook

from app.parsers.base import ParseError
from app.parsers.dispatch import parse_upload, sniff


def _xlsx_bytes() -> bytes:
    wb = Workbook()
    wb.active.append(["a", "b"])
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_sniff_xlsx():
    data = _xlsx_bytes()
    assert sniff(data, "foo.xlsx") == "xlsx"
    assert sniff(data, "FOO.XLSX") == "xlsx"


def test_sniff_zip_without_xlsx_ext_is_unknown():
    data = _xlsx_bytes()
    # 同样的 zip 头但文件名不是 .xlsx —— 我们不支持 zip
    assert sniff(data, "foo.zip") == "unknown"


def test_sniff_csv_utf8():
    data = b"a,b,c\n1,2,3\n"
    assert sniff(data, "x.csv") == "csv"


def test_sniff_csv_utf8_bom():
    data = "﻿a,b\n".encode("utf-8-sig")
    assert sniff(data, "x.csv") == "csv"


def test_sniff_csv_gbk():
    data = "交易号,金额\nT1,1.00\n".encode("gbk")
    assert sniff(data, "x.csv") == "csv"


@pytest.mark.parametrize("encoding", ["utf-8", "gbk"])
def test_sniff_csv_with_multibyte_character_at_probe_boundary(encoding):
    data = b"a" * 4095 + "交易号,金额\nT1,1.00\n".encode(encoding)
    assert sniff(data, "x.csv") == "csv"


def test_sniff_binary_garbage_is_unknown():
    data = bytes([0xFF, 0xFE, 0xFD, 0xFC, 0x00, 0x80, 0x81, 0x82] * 8)
    assert sniff(data, "x.bin") == "unknown"


def test_parse_upload_unknown_raises():
    data = bytes([0xFF, 0xFE, 0xFD, 0xFC] * 16)
    with pytest.raises(ParseError, match="不支持的文件格式"):
        parse_upload(data, "x.bin", "alipay", owner=None)
