# PRD 00 · 产品总览

## 一句话定位

让用户上传支付宝/微信账单 CSV/XLSX，按自己在 Web 上配置的策略 Pipeline 自动分类，并以报表、明细、资产页面呈现。目前只提供 AI 分类策略类型。

## 目标用户

- 个人/家庭记账用户
- 关键诉求：账单要按自己习惯的"业务分类"自动归类，不想每月手工标
- 期望可控：规则改了能复跑；AI 用哪家、用什么模型自己选

## 不做（MVP 范围外）

- 自动同步银行流水（目前仅支持手动导出 CSV/XLSX）
- 团队/共享账本
- 移动端原生 App
- 飞书旧数据自动迁移

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
