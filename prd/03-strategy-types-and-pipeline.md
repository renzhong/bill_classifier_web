# PRD 03 · 策略类型与 Pipeline

## 用户故事
- 浏览系统内置的全部策略类型，了解每种的作用
- 把策略类型实例化（填参数）加入我的 Pipeline，可拖拽排序
- 启停某条步骤、改参数后能重跑分类
- 看每条账单是被哪条策略命中的

## 内置策略类型
完整清单与参数 → [docs/strategy-types.md](../docs/strategy-types.md)。MVP 内置 12 种（含 ai_classify）。

## 页面
- `/settings/pipeline`：
  - 左侧：策略类型卡片（type_key + display_name + description + "添加"按钮）
  - 右侧：当前 Pipeline 步骤列表（拖拽排序、启停 switch、点击编辑参数、删除）
  - 参数表单按 `param_schema`（JSONSchema）动态渲染

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
- 同一策略类型可实例化多次（如 3 个 substring_match 用不同字典）
- 调换顺序后重分类，结果按新顺序生效
- 禁用某步骤后，该步骤不参与执行
- 参数不合法被 `validate_params()` 拒绝

## 不做
- 步骤分组 / 子流程
- 条件分支
