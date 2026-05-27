# PRD 07 · 报表

## 用户故事
- 看全年每月收入/支出/结余柱状对比
- 看某月汇总：总支出 / 各类合计 / 资产合计 / 净值
- 看某月分类汇总：每类支出金额 + 占比饼图 + 明细联动
- 看某月资产结余（基于 assets 表 + bills 收支推导）

## 页面
- `/reports/yearly`：year 选择 + ECharts 柱状（每月 income vs expense）+ 年度合计卡
- `/reports/monthly`：month 选择 + 卡片网格（支出/收入/结余/资产/净值）
- `/reports/category`：month 选择 + 饼图 + 表格（点击类别跳明细页过滤）

## API
- `GET /api/v1/reports/yearly?year=2026`
- `GET /api/v1/reports/monthly?month=2026-05`
- `GET /api/v1/reports/category-summary?month=2026-05`
- `GET /api/v1/reports/balance?month=2026-05`

## 实现要点
- 利用 `bills.bill_month` 生成列做 GROUP BY，避免全表扫
- `lifecycle != 'skipped'` 才入统计
- 收入支出口径：`amount * (bill_type==income ? +1 : -1)`，跨月退款单独标识
- 资产合计：拿 `assets` 当月最新快照按 asset_type 汇总

## 验收
- 空账户访问报表页 → 友好空状态，引导上传
- 月份切换响应迅速（<300ms）
- 数字与明细页过滤后求和一致

## 不做
- 自定义维度（按 tag/按 owner）的高级报表
- 导出 PDF
