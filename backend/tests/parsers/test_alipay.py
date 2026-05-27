"""支付宝 parser 单测：fixture 全用最小化、与真实账单无关的合成数据"""
from decimal import Decimal

import pytest

from app.parsers.alipay import AlipayParser
from app.parsers.base import ParseError


def _build(rows: list[list[str]], encoding: str = "gbk") -> bytes:
    text = "\n".join(",".join(r) for r in rows) + "\n"
    return text.encode(encoding)


HEADER = [
    "流水号", "交易号", "交易创建时间", "付款时间", "最近修改时间",
    "交易来源地", "类型", "交易对方", "商品名称", "金额(元)", "收/支", "状态",
]


def test_basic_rows():
    rows = [
        ["支付宝交易记录明细查询"],
        ["账号", "test@example.com"],
        ["------"],
        HEADER,
        ["S1", "T1001", "2026-01-05 12:00:00", "2026-01-05 12:00:30", "", "WEB", "即时", "店铺甲", "拿铁", "18.00", "支出", "交易成功"],
        ["S2", "T1002", "2026-01-06 08:30:00", "", "", "WEB", "即时", "工资发放方", "工资", "10000.00", "收入", "交易成功"],
        ["S3", "T1003", "2026-01-07 09:00:00", "2026-01-07 09:00:10", "", "WEB", "即时", "退款方", "退款", "5.00", "不计收支", "交易关闭"],
        ["------"],
        ["导出于 2026-02-01"],
    ]
    result = AlipayParser().parse(_build(rows), owner="alice")
    assert len(result.items) == 3
    assert result.skipped_rows == 0

    a, b, c = result.items
    assert a.source == "alipay"
    assert a.order_id == "T1001"
    assert a.payee == "店铺甲"
    assert a.item_name == "拿铁"
    assert a.amount == Decimal("18.00")
    assert a.bill_type == "expense"
    assert a.bill_time.strftime("%Y-%m-%d %H:%M:%S") == "2026-01-05 12:00:00"
    assert a.owner == "alice"

    assert b.bill_type == "income"
    assert c.bill_type == "other"


def test_falls_back_to_creation_time_when_payment_time_empty():
    rows = [
        ["------"],
        HEADER,
        ["S1", "T1", "2026-01-05 12:00:00", "", "", "", "", "X", "Y", "1.00", "支出", ""],
        ["------"],
    ]
    result = AlipayParser().parse(_build(rows))
    assert result.items[0].bill_time.strftime("%H:%M") == "12:00"


def test_skips_bad_rows_without_breaking_others():
    rows = [
        ["------"],
        HEADER,
        ["S1", "T1", "BAD_TIME", "", "", "", "", "P", "I", "1.00", "支出", ""],
        ["S2", "T2", "2026-01-05 12:00:00", "", "", "", "", "P", "I", "abc", "支出", ""],
        ["S3", "T3", "2026-01-05 12:00:00", "", "", "", "", "OK", "OK", "9.99", "支出", ""],
        ["------"],
    ]
    result = AlipayParser().parse(_build(rows))
    assert len(result.items) == 1
    assert result.items[0].order_id == "T3"
    assert result.skipped_rows == 2
    assert len(result.errors) == 2


def test_missing_columns_raises():
    rows = [["------"], ["列1", "列2"], ["a", "b"], ["------"]]
    with pytest.raises(ParseError):
        AlipayParser().parse(_build(rows))
