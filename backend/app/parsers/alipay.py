"""支付宝账单 CSV 解析

支付宝导出的 CSV 通常是 GBK 编码，头尾有 ``------`` 分隔行包裹真正的数据区。
本实现按表头列名匹配列位置，不依赖固定下标，以适应不同导出版本。
"""
from __future__ import annotations

from app.parsers._common import (
    get_col,
    index_map,
    normalize_bill_type,
    parse_amount,
    parse_time,
    read_rows,
)
from app.parsers.base import BillItem, ParseError, Parser, ParseResult

REQUIRED_COLS = ["交易号", "商品", "金额"]


class AlipayParser(Parser):
    source = "alipay"

    def parse(self, data: bytes, owner: str | None = None) -> ParseResult:
        rows = read_rows(data, prefer_encoding="gbk")
        return self.parse_rows(rows, owner=owner)

    def parse_rows(self, rows: list[list[str]], owner: str | None = None) -> ParseResult:
        if not rows:
            raise ParseError("empty data")

        data_block = _extract_data_block(rows)
        if not data_block:
            raise ParseError("alipay data block not found (missing ------ delimiters)")

        header, body = data_block[0], data_block[1:]
        cols = index_map(header)
        missing = [c for c in REQUIRED_COLS if not any(c in k for k in cols)]
        if missing:
            raise ParseError(f"alipay missing required columns: {missing}")

        # 模糊匹配（不同导出版本字段名略有差异）
        idx_order = _find_index(cols, ["交易号", "流水号"])
        idx_payee = _find_index(cols, ["交易对方", "对方账号"])
        idx_item = _find_index(cols, ["商品说明", "商品名称"])
        idx_amount = _find_index(cols, ["金额(元)", "金额"])
        idx_bill_type = _find_index(cols, ["收/支"])
        idx_time = _find_index(cols, ["交易创建时间", "交易时间"])
        idx_time_fallback = _find_index(cols, ["付款时间"])

        items: list[BillItem] = []
        errors: list[str] = []
        skipped = 0

        for line_no, row in enumerate(body, start=2):
            if not any(row):
                skipped += 1
                continue
            try:
                time_text = get_col(row, idx_time) or get_col(row, idx_time_fallback)
                items.append(
                    BillItem(
                        source="alipay",
                        order_id=get_col(row, idx_order) or None,
                        payee=get_col(row, idx_payee) or None,
                        item_name=get_col(row, idx_item) or None,
                        amount=parse_amount(get_col(row, idx_amount)),
                        bill_type=normalize_bill_type(get_col(row, idx_bill_type)),
                        bill_time=parse_time(time_text),
                        owner=owner,
                        raw={"line": line_no},
                    )
                )
            except Exception as e:
                errors.append(f"line {line_no}: {e}")
                skipped += 1

        return ParseResult(items=items, skipped_rows=skipped, errors=errors)


def _extract_data_block(rows: list[list[str]]) -> list[list[str]]:
    """支付宝 CSV 用 ``------...`` 行包裹数据区，提取其中部分（含表头）"""
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
    # 若没有分隔行，则把整张表视为数据区
    if not out:
        return rows
    return out


def _find_index(cols: dict[str, int], candidates: list[str]) -> int | None:
    """按 candidates 的顺序查找列，前面的优先级更高"""
    for cand in candidates:
        for k, idx in cols.items():
            if cand in k:
                return idx
    return None
