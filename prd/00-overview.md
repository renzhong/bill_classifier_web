# PRD 00 · 产品总览

## 一句话定位

让用户通过弹窗上传支付宝/微信账单 CSV/XLSX，先预览解析结果，再点击按钮运行测试分类规则、行内修正并归档，然后查看月度分类花费、资产、投资和收入。当前代码只提供 AI 分类策略类型。

## 目标用户

- 个人/家庭记账用户
- 关键诉求：账单要按自己习惯的"业务分类"自动归类，不想每月手工标
- 期望可控：规则改了能复跑；AI 用哪家、用什么模型自己选

## 不做（MVP 范围外）

- 自动同步银行流水（目前仅支持手动导出 CSV/XLSX）
- 团队/共享账本
- 移动端原生 App
- 飞书旧数据自动迁移

## 目标页面结构

1. **账单处理**：点击上传按钮在弹窗中选择文件、平台和可选标签；临时表格查看解析结果，点击按钮分类、行内修改类别并归档；同页维护分类项。规则管理页本轮暂缓。
2. **每月账单分类汇总**：选择月份，查看每个分类的花费和对应明细。
3. **每月资产汇总**：先创建可命名的资产项和负债项；新月沿用项目清单，只填写各项当月金额并查看汇总。投资项估值自动计入。没有额外的独立资产汇总页。
4. **投资**：按投资项查看本金、逐月买入与卖出、现值及当月盈亏，并可新增投资项。
5. **收入**：逐笔记录时间与金额，查看月收入和年收入汇总。

类别、Tag、Pipeline 和 AI 配置等设置页面仍作为账单处理的辅助入口。目标页面结构是规划，当前可用页面以代码和 `docs/` 为准。

## 模块清单

| # | 模块 | PRD |
|---|---|---|
| 1 | 账号 + 邀请码 | [01-auth-and-invitation.md](./01-auth-and-invitation.md) |
| 2 | 账单上传与解析 | [02-bill-upload-and-parse.md](./02-bill-upload-and-parse.md) |
| 3 | 策略类型 + Pipeline | [03-strategy-types-and-pipeline.md](./03-strategy-types-and-pipeline.md) |
| 4 | 类别 / Tag / 字典 | [04-categories-tags-dicts.md](./04-categories-tags-dicts.md) |
| 5 | AI Provider / 策略 | [05-ai-providers-and-strategies.md](./05-ai-providers-and-strategies.md) |
| 6 | 账单明细页 | [06-bills-detail-page.md](./06-bills-detail-page.md) |
| 7 | 报表 | [07-reports.md](./07-reports.md) |
| 8 | 资产 / 收入 | [08-assets-and-incomes.md](./08-assets-and-incomes.md) |
| 9 | 部署 | [09-deployment.md](./09-deployment.md) |
| 10 | 投资 | [10-investments.md](./10-investments.md) |
