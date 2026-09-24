# 架构方案 — Bill Classifier Web

## 1. 项目背景

把 `~/github/bill_classifier` Python CLI 工具重构为一套**通用账单分类 Web 系统**。原工具把业务规则硬编码进代码与飞书表，新系统改为：**代码只提供能力，所有规则由用户在 Web 上配置**，多租户、可上线。

---

## 2. 系统拓扑

```
┌─────────────────────────────────────────────────────────────┐
│  浏览器（Vue 3 SPA）                                         │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS
┌────────────────────▼────────────────────────────────────────┐
│  prod: 宿主 nginx (443)                                      │
│   ├─ / → /opt/bill-classifier-web/frontend/dist (static)    │
│   └─ /api/ → 127.0.0.1:8080 (backend container)             │
│  test: nginx 容器 :8088 反代 backend:8000 + frontend:5173    │
│  dev : vite dev server :5173 + uvicorn :8000                │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│  FastAPI backend (uvicorn :8000)                            │
│   ├─ auth / categories / tags / dicts / pipeline            │
│   ├─ parsers (alipay, wechat)                               │
│   ├─ classify engine + strategy_types (插件式)               │
│   ├─ ai providers (openai_compat / claude / gemini)         │
│   ├─ bills / reports / assets / investments / incomes       │
│   └─ tasks (FastAPI BackgroundTasks)                        │
└────────────────────┬────────────────────────────────────────┘
                     │ async SQLAlchemy
┌────────────────────▼────────────────────────────────────────┐
│  MySQL 8 (单库)                                              │
│   users / invitation_codes / categories / tags / user_dicts │
│   pipeline_steps / upload_tasks / bills / bill_tags         │
│   ai_credentials / ai_strategies / monthly_incomes / assets │
│   asset_items / asset_month_values / investment_items       │
│   investment_months / income_entries                        │
└─────────────────────────────────────────────────────────────┘
                     │ HTTPS
┌────────────────────▼────────────────────────────────────────┐
│  External AI: openai / qwen / glm / kimi / claude / gemini   │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 技术选型与权衡

| 维度 | 选型 | 理由 |
|---|---|---|
| 前端 | Vue 3 + TS + Vite + Naive UI + Pinia + Vue Router 4 | 表单/表格密集后台，Naive UI 控件齐全；与 ClashConfigGen 同栈，部署模式可复用 |
| 后端 | FastAPI + Pydantic v2 + SQLAlchemy 2.0 async + asyncmy | async 原生；AI SDK 生态最完整；类型约束强 |
| 包管理 | uv | 速度快，与多阶段 Dockerfile 配合好 |
| 数据库 | MySQL 8（单库，**MVP 不分表**） | 用户级数据量级足够；schema 预留 `(user_id, ...)` 前导索引，未来分表零成本 |
| 异步 | FastAPI BackgroundTasks（同进程）+ asyncio.gather | MVP 无需 Redis；AI 调用天然并发 |
| 鉴权 | JWT + Argon2 + 邀请码注册 | 简单稳定；邀请码控制扩张 |
| 密钥 | Fernet 对称加密 + 环境变量注入 | AI api_key 落库加密；MVP 不上 KMS |

---

## 4. 后端模块

```
backend/app/
├── core/         config / db / security / deps / logging / response
├── auth/         注册（验邀请码）/登录/JWT/邀请码管理
├── parsers/      base + alipay + wechat（UploadFile → list[BillItem]）
├── categories/   类别 CRUD
├── tags/         tag CRUD
├── dicts/        user_dicts + entries CRUD + 批量导入
├── pipeline/     pipeline_steps CRUD + 排序 + 策略类型元数据查询
├── classify/
│   ├── bill_item.py   in-memory DTO
│   ├── context.py     执行上下文（user_id、字典缓存、AI service 注入）
│   ├── engine.py      Pipeline runner
│   └── strategy_types/<name>.py  各内置策略类型
├── ai/
│   ├── base.py        LLMProvider ABC
│   ├── registry.py    PROVIDER_REGISTRY
│   ├── providers/openai_compat.py | claude.py | gemini.py
│   ├── prompt_template.py
│   └── service.py     业务封装
├── tasks/        BackgroundTasks 账单解析 runner
├── bills/        临时批次/手动测试分类/归档/明细与改类
├── reports/      yearly / monthly / category-summary / balance
├── assets/       资产项/负债项与每月金额
├── investments/  投资项/每月买卖、估值与盈亏
├── incomes/      逐笔收入与旧月度收入
└── api/v1/       router 聚合
```

依赖方向：`api → service → models / classify / ai`。`core` 被所有人依赖。

---

## 5. 数据模型（ER 简图）

```
users ─┬─< invitation_codes
       ├─< categories ─< user_dict_entries >─ user_dicts
       ├─< tags ─< bill_tags >─ bills
       ├─< pipeline_steps >─< bills.classify_strategy_id
       ├─< upload_tasks ─< bills
       ├─< ai_credentials ─< ai_strategies
       ├─< monthly_incomes, income_entries
       ├─< assets (旧快照)
       ├─< asset_items ─< asset_month_values
       └─< investment_items ─< investment_months
```

完整字段定义见 `migrations/versions/0001_initial_schema.py`，关键设计：

- `bills.bill_month`：MySQL 生成列 `DATE_FORMAT(bill_time, '%Y-%m')`，月度报表零成本聚合
- `bills` UNIQUE `(user_id, source, order_id)`：上传幂等
- 无交易单号的账单另存 `dedup_hash` 唯一摘要；旧账单按解析字段查重
- `bills.archived` 与分类 `lifecycle` 独立：新上传先临时保存，旧数据迁移为已归档；只有已归档账单进入报表
- `asset_month_values` 缺行表示待填写，金额 0 表示明确录入 0；投资估值仅从 `investment_months` 投影。投资项可关联已有手工资产项，关联后该手工项在投资月份不再计入合计，避免重复计入
- 旧 `assets` 保留并迁入可复用资产项，旧 `monthly_incomes` 保留月度粒度，不伪造收入日期
- `pipeline_steps.params` JSON：策略类型自定义参数，由 StrategyType 校验
- 所有用户级表 `user_id` 列建索引

---

## 6. 通用策略引擎

> **现状提醒**：代码中仅实现 `ai_classify` 一个策略类型。其他类型只是[候选](./docs/strategy-types.md)；新增类型需注册后端实现，并检查前端参数表单是否支持其字段。

**核心抽象**：

```python
class StrategyType(ABC):
    type_key: str
    display_name: str
    description: str
    param_schema: dict     # JSONSchema，前端用它自动渲染参数表单

    def validate_params(self, params: dict) -> None: ...
    async def run(self, items: list[BillItem], params: dict, ctx: Context) -> list[BillItem]: ...
```

**执行模型**：

```
upload CSV/XLSX → parsers → list[BillItem]
           → 保存临时 bills（含不可逐笔修改的上传标签）
           → 用户点击“开始分类”：仅对非人工改类的临时支出账单运行
              名称正则“地铁|公交 → 交通”测试规则
           → 用户在临时表格直接修正类别 → 点击归档
           → 归档账单按交易时间进入月份查询和报表
```

用户配置的 Pipeline 和 AI 组件仍保留，但当前上传流程不会自动调用。单条
`/bills/{id}/reclassify` 仍可显式运行现有 Pipeline，且人工改类账单不会交给 AI。
本轮没有规则管理页，也未把测试正则注册为通用策略类型。

**为何 param_schema 是 JSONSchema**：前端据此渲染当前支持的参数类型；新字段类型需扩展表单组件。

**MVP 仅内置 `ai_classify` 一种策略**。其他策略类型（精确匹配、子串匹配、合并、扩散等）将根据实际需求按需单独迭代。引擎本身已具备完整扩展性。详细见 [docs/strategy-types.md](./docs/strategy-types.md)。

---

## 7. AI 抽象层

```python
class LLMProvider(ABC):
    provider_key: str  # openai / qwen / claude / gemini / glm / kimi
    async def chat(self, *, prompt: str, model: str, api_key: str, base_url: str | None) -> str: ...
```

- **OpenAI 兼容族**（openai / qwen / glm / kimi）：共用一份 `openai_compat.py`，注册表里登记不同 entry（提供默认 base_url / 推荐 model）
- **Claude**：独立 adapter（anthropic SDK）
- **Gemini**：独立 adapter（google-generativeai SDK）

Prompt 由 `prompt_template.py` 的预设 template + 用户在 `ai_strategies.strategy_text` 中填写的多条策略文本拼接而成。前端「AI 策略」页面有"最终 prompt 预览"区域。

---

## 8. 前端架构

```
src/
├── main.ts / App.vue (NConfigProvider + 各 Provider)
├── router/index.ts          路由 + JWT 守卫
├── stores/                  Pinia: user / meta
├── api/                     axios 实例 + 模块化 client
├── views/                   与路由一一对应
├── components/              AppLayout / EChart / StrategyParamForm
└── styles/global.css
```

路由结构与页面清单见 README & arch 各 section。

---

## 9. 部署架构

| 环境 | 前端 | 后端 | DB | nginx |
|---|---|---|---|---|
| dev | vite :5173 | uvicorn :8000 容器 reload | mysql:8 容器 | vite proxy |
| test | vite 容器 | uvicorn 容器 | mysql 容器 | nginx 容器 :8088 |
| prod | 宿主静态目录 | uvicorn 容器 :127.0.0.1:8080 | 宿主/RDS | 宿主 nginx :443 |

详见 `docker-compose.yml` / `docker-compose.prod.yml` / `nginx/sites/*.conf`。

---

## 10. 与原 `bill_classifier` 的关系

**仅作为参考资料**：理解 CSV 字段位置（`bill_classifier/bill.py`）、归纳通用策略类型（`bill_classifier/classifiers/*` 的思想）、OpenAI 兼容调用模式（`classifier_gpt.py`）。

**不复用**：任何业务规则代码、任何业务数据（分类枚举、关键词字典、prompt 模板示例）、所有飞书集成。新系统是 0 起步的通用平台。

---

## 11. 演进方向（MVP 不做）

- Arq + Redis 异步队列（长任务 / 多用户并发激增时）
- 按 user_id 分库分表（单表过亿时）
- 策略模板包（用户互相分享 / 系统内置可选包，但仍由用户主动导入）
- AI 调用缓存层
- 移动端 H5
- 飞书旧数据导入工具（针对原工具用户）
