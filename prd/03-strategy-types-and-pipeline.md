# PRD 03 · 策略类型与 Pipeline

## 用户故事
- 浏览系统内置的全部策略类型，了解每种的作用
- 把策略类型实例化（填参数）加入我的 Pipeline，用上下按钮调整顺序
- 启停某条步骤、改参数后可在账单明细中逐笔重分类
- 看每条账单是被哪条策略命中的

## 内置策略类型

**MVP 仅内置 1 种：`ai_classify`**（调 LLM 分类，规则文本来自用户的 AI 策略）。其他策略类型按需后续单独迭代，不预先实现。完整说明 → [docs/strategy-types.md](../docs/strategy-types.md)。

引擎本身（StrategyType ABC + 注册器 + Pipeline runner）已具备扩展接口；新增策略类型需实现并注册后端策略，同时核对前端参数表单是否支持所需字段类型。

## 页面
- `/settings/pipeline`：
  - 左侧：策略类型卡片（type_key + display_name + description + "添加"按钮）
  - 右侧：当前 Pipeline 步骤列表（上下按钮排序、启停 switch、点击编辑参数、删除）
  - 参数表单按 `param_schema`（JSONSchema）渲染已支持的字段类型

## API
- `GET /api/v1/pipeline/strategy-types` → `[{type_key, display_name, description, param_schema}]`
- `GET /api/v1/pipeline/steps`
- `POST /api/v1/pipeline/steps`
- `PATCH /api/v1/pipeline/steps/:id`
- `DELETE /api/v1/pipeline/steps/:id`
- `POST /api/v1/pipeline/steps/reorder` body `{order: [{id, sort_order}]}`

## 数据模型
- `pipeline_steps(id, user_id, strategy_type, display_name, params JSON, sort_order, enabled, ts)`

## 验收
- 同一策略类型可实例化多次
- 调换顺序后重分类，结果按新顺序生效
- 禁用某步骤后，该步骤不参与执行
- 参数不合法被 `validate_params()` 拒绝
- `ai_classify` 步骤可指定不同 strategy_id，组合不同凭据 / prompt 文本

## 不做
- 步骤分组 / 子流程
- 条件分支
