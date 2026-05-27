"""微信 parser 单测"""
from decimal import Decimal

import pytest

from app.parsers.base import ParseError
from app.parsers.wechat import WechatParser


def _build(rows: list[list[str]]) -> bytes:
    text = "\n".join(",".join(r) for r in rows) + "\n"
    return text.encode("utf-8")


HEADER = ["交易时间", "交易类型", "交易对方", "商品", "收/支", "金额(元)", "支付方式", "当前状态", "交易单号", "商户单号", "备注"]


def test_basic_rows():
    rows = [
        ["微信支付账单明细"],
        ["开始时间", "2026-01-01", "结束时间", "2026-01-31"],
        ["------"],
        HEADER,
        ["2026-01-05 12:00:00", "商户消费", "店铺甲", "拿铁", "支出", "¥18.00", "零钱", "支付成功", "4200001001", "M001", "/"],
        ["2026-01-06 08:30:00", "转账", "好友", "/", "收入", "¥50.00", "零钱", "已收钱", "4200001002", "M002", "/"],
        ["------"],
    ]
    result = WechatParser().parse(_build(rows), owner="bob")
    assert len(result.items) == 2
    a, b = result.items
    assert a.source == "wechat"
    assert a.amount == Decimal("18.00")
    assert a.bill_type == "expense"
    assert a.owner == "bob"
    assert b.amount == Decimal("50.00")
    assert b.bill_type == "income"


def test_refund_subtracts_amount():
    rows = [
        ["------"],
        HEADER,
        ["2026-01-05 12:00:00", "消费", "店铺A", "商品X", "支出", "¥100.00", "零钱", "已退款(¥30.00)", "T1", "M", ""],
        ["------"],
    ]
    result = WechatParser().parse(_build(rows))
    assert result.items[0].amount == Decimal("70.00")


def test_supports_slash_date_format():
    rows = [
        ["------"],
        HEADER,
        ["2026/01/05 12:00", "消费", "店铺", "商品", "支出", "¥1.00", "零钱", "支付成功", "T1", "M", ""],
        ["------"],
    ]
    result = WechatParser().parse(_build(rows))
    assert result.items[0].bill_time.strftime("%Y-%m-%d %H:%M") == "2026-01-05 12:00"


def test_missing_columns_raises():
    rows = [["------"], ["a", "b"], ["x", "y"], ["------"]]
    with pytest.raises(ParseError):
        WechatParser().parse(_build(rows))
