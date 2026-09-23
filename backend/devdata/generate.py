"""Generate both providers' upload files from a single reviewed fixture set."""

import argparse
import csv
import json
from datetime import datetime
from io import BytesIO, StringIO
from pathlib import Path

from openpyxl import Workbook

DATA_DIR = Path(__file__).parent


def cases():
    return json.loads((DATA_DIR / "cases.json").read_text())


def rows(source):
    if source == "wechat":
        yield ["交易时间", "交易对方", "商品", "收/支", "金额(元)", "当前状态", "交易单号"]
        for case in cases():
            yield [
                case["time"],
                case["payee"],
                case["item"],
                case["type"],
                case["amount"],
                case["status"],
                case["order_id"],
            ]
    elif source == "alipay":
        yield ["交易创建时间", "交易对方", "商品说明", "收/支", "金额(元)", "交易号"]
        for case in cases():
            yield [
                case["time"],
                case["payee"],
                case["item"],
                case["type"],
                case["expected_amount"],
                case["order_id"],
            ]
    else:
        raise ValueError(f"unsupported source: {source}")


def xlsx_bytes(source):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "合成测试账单"
    for index, row in enumerate(rows(source)):
        if index:
            row[0] = datetime.fromisoformat(row[0])
            row[4] = float(row[4])
        sheet.append(row)
    output = BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


def generate(output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    for source, encoding in (("wechat", "utf-8-sig"), ("alipay", "gbk")):
        (output_dir / f"{source}.xlsx").write_bytes(xlsx_bytes(source))
        output = StringIO()
        csv.writer(output).writerows(rows(source))
        (output_dir / f"{source}.csv").write_bytes(output.getvalue().encode(encoding))
    (output_dir / "expected.json").write_text(json.dumps(cases(), ensure_ascii=False, indent=2) + "\n")
    print(f"测试账单和预期分类：{output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    generate(parser.parse_args().output_dir)
