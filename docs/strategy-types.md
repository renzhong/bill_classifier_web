# 内置策略类型清单

每种策略类型在 M3 实现。`param_schema` 用 JSONSchema 表达，前端据此自动渲染表单。

## 命名约定
- `type_key`: 小写下划线，全局唯一
- `display_name`: 中文展示名
- `description`: 一句话用途
- `param_schema`: JSONSchema（type=object）

## 清单

### exact_match
精确匹配字段 = 字典 key 时打类别。
```json
{
  "target_field": {"enum": ["payee", "item_name"]},
  "dict_id": {"type": "integer"}
}
```

### substring_match
字段包含字典中某 key（子串）时打类别。参数同上。

### regex_match
字段匹配指定正则时打类别。
```json
{
  "target_field": {"enum": ["payee", "item_name"]},
  "pattern": {"type": "string"},
  "category_id": {"type": "integer"}
}
```

### skip_by_keyword
命中关键词的条目跳过后续步骤。
```json
{
  "target_field": {"enum": ["payee", "item_name"]},
  "keywords": {"type": "array", "items": {"type": "string"}},
  "reason": {"type": "string"}
}
```

### skip_by_bill_type
按账单类型跳过。
```json
{"bill_types": {"type": "array", "items": {"enum": ["income", "other", "expense"]}}}
```

### merge_by_payee_window
同 payee 在 N 秒内的多条小额合并为一条。
```json
{
  "window_seconds": {"type": "integer", "minimum": 1},
  "min_count": {"type": "integer", "minimum": 2},
  "amount_threshold": {"type": "number"}
}
```

### merge_refund_by_order
同 order_id 在 ±N 天内的退款合并到原单（amount 抵扣）。
```json
{"window_days": {"type": "integer", "minimum": 1}}
```

### time_window_spread
某锚类已分类的条目，向 ±N 分钟邻近的未分类条目扩散同一类别。
```json
{
  "anchor_category_id": {"type": "integer"},
  "window_minutes": {"type": "integer"},
  "direction": {"enum": ["both", "before", "after"]}
}
```

### neighbor_inference
命中"源关键字"的条目，向时间邻近的条目承袭其分类。
```json
{
  "source_keywords": {"type": "array", "items": {"type": "string"}},
  "target_field": {"enum": ["payee", "item_name"]},
  "window_minutes": {"type": "integer"}
}
```

### cross_month_refund
跨月退款（>= N 天）标记为 `cross_month_refund` 单独处理。
```json
{"min_days": {"type": "integer", "minimum": 1}}
```

### merge_extra_amount
同订单的子金额项合并到主项（如购物金、立减等加成到主交易）。
```json
{
  "field_pattern": {"type": "string"},
  "window_seconds": {"type": "integer"}
}
```

### ai_classify
LLM 兜底分类。
```json
{
  "strategy_id": {"type": "integer"},
  "only_unclassified": {"type": "boolean", "default": true}
}
```

## 添加新类型
见 [CLAUDE.md §5.1](../CLAUDE.md)。
