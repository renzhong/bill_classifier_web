# PRD 02 · 账单上传与解析

## 用户故事
- 上传一份月度支付宝/微信账单 CSV，系统自动解析并入库
- 上传时可选 source、加 tag、填账单归属人（owner）
- 重复上传同一份不会产生重复账单
- 上传任务可查看进度与失败原因

## 页面
- `/bills/upload`：文件 + source 单选（alipay/wechat）+ owner 文本 + tag 多选
- `/bills/tasks`：列表 + 状态 + 解析行数 / 分类行数 / 错误信息

## API
- `POST /api/v1/bills/upload`（multipart）
- `GET /api/v1/upload-tasks`
- `GET /api/v1/upload-tasks/:id`

## 数据模型
- `upload_tasks(id, user_id, source, filename, file_size, status, total_rows, classified_rows, error_msg, tag_ids JSON, owner_label, ts)`
- `bills(...)` UNIQUE `(user_id, source, order_id)` → 静默跳过重复

## Parser 行为
- 支付宝 CSV：GBK 编码，字段位置见 [docs/parser-spec.md](../docs/parser-spec.md)
- 微信 CSV：UTF-8 编码
- 跳过头部说明行，从第一条数据行开始解析
- 时间字符串规整为 `datetime`；金额规整为 `Decimal(12,2)`

## 验收
- 真实月度 CSV 上传 → 状态 done，明细页能看到数据
- 重复上传同一份 → upload_task 报告 "跳过 N 条已存在"
- 文件超出 `BCW_UPLOAD_MAX_BYTES` → 413
- 错误编码/缺字段 → status=failed + error_msg

## 不做
- 自动判断 source（必须用户选）
- 多文件批量上传（先单文件）
