# 策略类型清单

## MVP 现状

**MVP 仅内置一种策略类型：[`ai_classify`](#ai_classify)。**

其他策略类型（精确匹配、子串匹配、合并、时间窗扩散等）将根据实际需求按需单独迭代，**不会一次性预先实现**。引擎本身（`StrategyType` ABC + 注册器 + Pipeline runner）已经具备完整扩展性，新增策略类型只需新增一个文件并 register，前端按 `param_schema` 自动渲染表单，无需任何前端改动。

## 命名约定

- `type_key`: 小写下划线，全局唯一
- `display_name`: 中文展示名
- `description`: 一句话用途
- `param_schema`: JSONSchema（type=object）

## `ai_classify`

调用大模型给账单分类。系统把用户在「AI 策略」中填写的多条文本规则拼入 prompt，对每条待分类账单单独发起一次推理。

```json
{
  "type": "object",
  "required": ["strategy_id"],
  "properties": {
    "strategy_id": {"type": "integer", "title": "AI 策略", "description": "选择 /settings/ai/strategies 中的一条策略"},
    "only_unclassified": {"type": "boolean", "title": "仅对未分类账单生效", "default": true},
    "max_concurrency": {"type": "integer", "title": "并发上限", "default": 4, "minimum": 1, "maximum": 32}
  }
}
```

行为：
- 默认只处理 `lifecycle == 'unprocessed'` 且 `category_id is None` 的账单
- 模型返回的类别必须在当前用户的 categories 中，否则视为未命中
- 单条调用失败（rate-limit / 网络）记录日志，不阻塞批次
- 并发由 `max_concurrency` 控制（asyncio.Semaphore）

提示词模板见 `backend/app/ai/prompt_template.py`，前端 `/settings/ai/strategies` 页面有"最终 prompt 预览"区域。

## 未来候选策略类型（仅作示例参考，**未实现**）

下列类型曾在早期 plan 中作为概念出现，**不要预先实现**。等真正有需求时再单独迭代每一个。

| 候选 type_key | 用途 |
|---|---|
| `exact_match` | 字段精确等于字典 key 时打类别 |
| `substring_match` | 字段包含字典 key 时打类别 |
| `regex_match` | 字段匹配正则时打类别 |
| `skip_by_keyword` | 命中关键词的条目跳过 |
| `skip_by_bill_type` | 按账单类型跳过 |
| `merge_by_payee_window` | 同 payee N 秒内合并 |
| `merge_refund_by_order` | 同订单 ±N 天退款合并 |
| `time_window_spread` | 已分类条目向邻近未分类扩散 |
| `neighbor_inference` | 命中"源关键字"的条目向邻近承袭分类 |
| `cross_month_refund` | 跨月退款标记 |
| `merge_extra_amount` | 同订单子项金额合并到主项 |

## 新增策略类型操作步骤

1. 在 `backend/app/classify/strategy_types/<your_type>.py` 中实现 `StrategyType` 子类：
   ```python
   class MyStrategy(StrategyType):
       type_key = "my_type"
       display_name = "我的策略"
       description = "..."
       param_schema = {...}
       def validate_params(self, params): ...
       async def run(self, items, params, ctx): ...
   ```
2. 在 `backend/app/classify/strategy_types/__init__.py` 中 `register(MyStrategy())`
3. 添加 `backend/tests/classify/test_<your_type>.py` 单测
4. 前端无需改动：`/settings/pipeline` 自动展示新策略卡片，按 `param_schema` 渲染参数表单
