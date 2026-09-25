# 账单 CSV / XLSX 字段约定

实现见 `backend/app/parsers/{alipay,wechat,dispatch}.py`。上传支持 CSV 和 XLSX；XLSX 首个 sheet 转为行后使用相同字段映射。

## 通用 BillItem DTO

```python
@dataclass
class BillItem:
    source: Literal["alipay", "wechat"]
    order_id: str | None
    payee: str | None              # 交易对象 / 收款方
    item_name: str | None          # 商品名称 / 描述
    amount: Decimal                # 正数
    bill_type: Literal["income", "expense", "other"]
    bill_time: datetime            # 不含 tz，统一 +08:00 解读
    owner: str | None              # 上传时用户填写的 owner_label
    raw: dict                      # 原始行（debug 用）
```

## 支付宝 CSV
- 编码：GBK（必要时 chardet 兜底）
- 头部含若干说明行，第一条数据行通常以 `"流水号"` 起
- 关键列（按表头匹配，不依赖位置硬编码）：
  - 交易号 → `order_id`
  - 商品说明 / 商品名称 → `item_name`
  - 交易对方 → `payee`
  - 金额（元） → `amount`
  - 收/支 → `bill_type`（"支出"→expense, "收入"→income, ""→other）
  - 交易时间 → `bill_time`

## 微信 CSV
- 编码：UTF-8
- 头部含 "微信支付账单明细" 等说明行
- 列：
  - 交易单号 → `order_id`
  - 商品 → `item_name`
  - 交易对方 → `payee`
  - 金额(元) → `amount`
  - 收/支 → `bill_type`
  - 交易时间 → `bill_time`

## 解析规则
- 跳过非数据行（含中文说明 / 空行）
- 金额去掉 `¥` `,` 等符号，转 Decimal
- 时间统一 `YYYY-MM-DD HH:MM:SS`
- 同 `(user_id, source, order_id)` 已存在 → 静默跳过（幂等）
- 没有交易单号时，按同用户、平台、交易时间、商户、名称、金额、收支及归属人逐字段去重；新记录也保存唯一摘要，防止并发重复导入
- 单行解析失败写入任务 `parse_errors`，摘要写入 `error_msg`；其他有效行继续保存为临时账单，任务为 `parsed`
- 文件格式不支持或缺少必需列时，整个任务标为 `failed`
- 解析完成后需由用户点击“开始分类”，并在临时表格核对/修正类别，最后点击“归档账单”；只有归档账单进入报表

## 不做
- 自动识别 source（必须用户在上传时选）
- 解析其他银行/平台账单（先聚焦两家）
