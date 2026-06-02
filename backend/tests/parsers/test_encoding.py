"""验证 csv 解析对 UTF-8 / UTF-8-BOM / GBK 三种编码都能通过"""
from __future__ import annotations

from app.parsers.alipay import AlipayParser
from app.parsers.wechat import WechatParser

ALIPAY_HEADER = "交易号,商家订单号,交易创建时间,付款时间,交易对方,商品名称,金额(元),收/支,交易状态"
ALIPAY_ROW = "T1,M1,2026-01-05 12:00:00,2026-01-05 12:00:30,店铺甲,拿铁,18.00,支出,交易成功"
ALIPAY_TEXT = (
    "支付宝交易记录明细查询\n"
    "账号:[a@b.com]\n"
    "------\n"
    f"{ALIPAY_HEADER}\n"
    f"{ALIPAY_ROW}\n"
    "------\n"
)

WECHAT_HEADER = "交易时间,交易类型,交易对方,商品,收/支,金额(元),支付方式,当前状态,交易单号,商户单号,备注"
WECHAT_ROW = "2026-01-05 12:00:00,消费,店铺,拿铁,支出,￥18.00,零钱,支付成功,T1,M1,/"
WECHAT_TEXT = (
    "微信支付账单明细\n"
    "------\n"
    f"{WECHAT_HEADER}\n"
    f"{WECHAT_ROW}\n"
    "------\n"
)


def test_alipay_gbk_and_utf8_give_same_result():
    r_gbk = AlipayParser().parse(ALIPAY_TEXT.encode("gbk"))
    r_utf = AlipayParser().parse(ALIPAY_TEXT.encode("utf-8"))
    assert len(r_gbk.items) == 1
    assert len(r_utf.items) == 1
    assert r_gbk.items[0].order_id == r_utf.items[0].order_id == "T1"
    assert r_gbk.items[0].amount == r_utf.items[0].amount


def test_wechat_utf8_and_utf8_sig_give_same_result():
    r_plain = WechatParser().parse(WECHAT_TEXT.encode("utf-8"))
    r_bom = WechatParser().parse(WECHAT_TEXT.encode("utf-8-sig"))
    assert len(r_plain.items) == 1
    assert len(r_bom.items) == 1
    assert r_plain.items[0].order_id == r_bom.items[0].order_id == "T1"


def test_wechat_gbk_also_works():
    """微信偏好 utf-8，但 detect_decode 应该能用 chardet 兜底到 gbk"""
    r = WechatParser().parse(WECHAT_TEXT.encode("gbk"))
    assert len(r.items) == 1
    assert r.items[0].order_id == "T1"
