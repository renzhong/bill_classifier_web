# PRD 08 · 资产 / 收入

## 用户故事
- 录入每月的资产快照（现金/存款/股票/基金/公司等），按账户细分；在资产汇总页查看各类资产与总金额
- 逐笔录入收入，按来源查看明细与收入合计
- 报表明确区分账单收入、另行录入的收入，以及资产快照；不使用笼统的“结余”概念

## 页面
- `/settings/assets`：月份切换、资产表格 CRUD；另需资产汇总页
- `/settings/incomes`：收入录入与明细列表；目前仅支持每月同一来源一条，逐笔录入仍待实现

## API
- `GET /api/v1/assets?month=YYYY-MM`
- `POST /api/v1/assets`
- `PATCH /api/v1/assets/:id`
- `DELETE /api/v1/assets/:id`
- `POST /api/v1/assets/copy` body `{from_month, to_month, overwrite?}` — 从某月复制资产快照到目标月
- `GET /api/v1/incomes?year= | ?month=`
- `POST /api/v1/incomes`
- `PATCH /api/v1/incomes/:id`
- `DELETE /api/v1/incomes/:id`

## 数据模型
- `assets(id, user_id, snapshot_month, asset_type, account_name, amount Numeric(14,2), remark)` INDEX `(user_id, snapshot_month)`
- 当前 `monthly_incomes(id, user_id, year_month, source, amount Numeric(12,2), remark)` UNIQUE `(user_id, year_month, source)`；逐笔收入的数据结构待明确日期粒度及同月同来源多笔场景

## 验收
- 复制上月快照功能（一键复制后微调）
- 当前同月 + 同 source 的收入 UNIQUE 冲突 → 友好提示；逐笔收入实现后应允许真实的多笔记录
- 数据修改后报表页刷新即生效

## 不做
- 自动从券商接口同步
- 净值曲线持久化（每次按需计算）
