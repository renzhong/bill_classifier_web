# PRD 08 · 资产 / 收入

## 用户故事
- 录入每月的资产快照（现金/活期/股票/基金/其他），按账户细分
- 录入每月的收入条目，可按来源拆分（工资/理财/其他）
- 报表页用这些数据计算结余与净值

## 页面
- `/settings/assets`：左侧月份切换，右侧表格 CRUD
- `/settings/incomes`：表格按 year_month + source 拆行

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
- `monthly_incomes(id, user_id, year_month, source, amount Numeric(12,2), remark)` UNIQUE `(user_id, year_month, source)`

## 验收
- 复制上月快照功能（一键复制后微调）
- 同月 + 同 source 的收入 UNIQUE 冲突 → 友好提示
- 数据修改后报表页刷新即生效

## 不做
- 自动从券商接口同步
- 净值曲线持久化（每次按需计算）
