# PRD 07 · 报表

## 用户故事
- 看全年每月账单收入、支出与收支差额的对比
- 看某月汇总：账单收支、已录入收入合计、各类支出、资产合计及较上月变化
- 看某月分类汇总：每类支出金额 + 占比饼图 + 明细联动
- 看某月资产结构与资产合计（基于该月录入的资产快照）

## 页面
- 每月账单分类汇总是目标页面结构中的账单花费入口；资产录入与资产汇总统一在 [PRD 08](./08-assets-and-incomes.md) 的每月资产汇总页完成，不另设资产汇总页。
- `/reports/yearly`：year 选择 + ECharts 柱状（每月 income vs expense）+ 年度合计卡
- `/reports/monthly`：month 选择 + 卡片网格（账单支出/账单收入/已录入收入/资产合计/资产较上月变化）
- `/reports/category`：month 选择 + 饼图 + 表格（点击类别跳明细页过滤）

## API
- `GET /api/v1/reports/yearly?year=2026`
- `GET /api/v1/reports/monthly?month=2026-05`
- `GET /api/v1/reports/category-summary?month=2026-05`
- `GET /api/v1/reports/balance?month=2026-05`

## 实现要点
- 利用 `bills.bill_month` 生成列做 GROUP BY，避免全表扫
- `lifecycle in ('skipped', 'cross_month_refund')` 一律剔除统计
- 收入支出口径：按 `bill_type` 拆 income / expense / other 三桶
- 资产合计：拿 `assets` 当月最新快照按 asset_type 汇总
- `monthly` 端点的"净值变化" = 当月资产合计 − 上月资产合计
- 前端用 echarts 5 + `components/EChart.vue` 通用封装；按需注册 `BarChart` / `PieChart` / `LineChart` 与必要组件，避免完整包打入 bundle

## 验收
- 空账户访问报表页 → 友好空状态，引导上传
- 月份切换响应迅速（<300ms）
- 数字与明细页过滤后求和一致

## 不做
- 自定义维度（按 tag/按 owner）的高级报表
- 导出 PDF
