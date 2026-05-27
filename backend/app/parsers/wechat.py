"""微信支付账单 CSV 解析

微信导出的 CSV 是 UTF-8 编码，同样用 ``------`` 行分隔数据区。
"""
from __future__ import annotations

import re
from decimal import Decimal

from app.parsers._common import (
    get_col,
    index_map,
    normalize_bill_type,
    parse_amount,
    parse_time,
    read_rows,
)
from app.parsers.base import BillItem, ParseError, ParseResult, Parser

REQUIRED_COLS = ["交易单号", "交易时间", "金额"]
REFUND_AMOUNT_PATTERN = re.compile(r"[¥￥]?(\d+(?:\.\d+)?)")


class WechatParser(Parser):
    source = "wechat"

    def parse(self, data: bytes, owner: str | None = None) -> ParseResult:
        rows = read_rows(data, prefer_encoding="utf-8")
        if not rows:
            raise ParseError("empty csv")

        data_block = _extract_data_block(rows)
        if not data_block:
            raise ParseError("wechat data block not found (missing ------ delimiters)")

        header, body = data_block[0], data_block[1:]
        cols = index_map(header)
        missing = [c for c in REQUIRED_COLS if not any(c in k for k in cols)]
        if missing:
            raise ParseError(f"wechat missing required columns: {missing}")

        idx_time = _find_index(cols, ["交易时间"])
        idx_payee = _find_index(cols, ["交易对方"])
        idx_item = _find_index(cols, ["商品"])
        idx_bill_type = _find_index(cols, ["收/支"])
        idx_amount = _find_index(cols, ["金额(元)", "金额"])
        idx_status = _find_index(cols, ["当前状态"])
        idx_order = _find_index(cols, ["交易单号"])

        items: list[BillItem] = []
        errors: list[str] = []
        skipped = 0

        for line_no, row in enumerate(body, start=2):
            if not any(row):
                skipped += 1
                continue
            try:
                amount = parse_amount(get_col(row, idx_amount))
                status = get_col(row, idx_status)
                if status.startswith("已退款"):
                    m = REFUND_AMOUNT_PATTERN.search(status)
                    if m:
                        refunded = Decimal(m.group(1))
                        amount = (amount - refunded).quantize(Decimal("0.01"))

                items.append(
                    BillItem(
                        source="wechat",
                        order_id=get_col(row, idx_order) or None,
                        payee=get_col(row, idx_payee) or None,
                        item_name=get_col(row, idx_item) or None,
                        amount=amount,
                        bill_type=normalize_bill_type(get_col(row, idx_bill_type)),
                        bill_time=parse_time(get_col(row, idx_time)),
                        owner=owner,
                        raw={"line": line_no, "status": status},
                    )
                )
            except Exception as e:
                errors.append(f"line {line_no}: {e}")
                skipped += 1

        return ParseResult(items=items, skipped_rows=skipped, errors=errors)


def _extract_data_block(rows: list[list[str]]) -> list[list[str]]:
    flag = False
    out: list[list[str]] = []
    for row in rows:
        first = (row[0] if row else "").strip()
        if first.startswith("------"):
            if not flag:
                flag = True
                continue
            else:
                break
        if flag:
            out.append(row)
    if not out:
        return rows
    return out


def _find_index(cols: dict[str, int], candidates: list[str]) -> int | None:
    for cand in candidates:
        for k, idx in cols.items():
            if cand in k:
                return idx
    return None
