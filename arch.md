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
│   ├─ bills / reports / assets / incomes                     │
│   └─ tasks (FastAPI BackgroundTasks)                        │
└────────────────────┬────────────────────────────────────────┘
                     │ async SQLAlchemy
┌────────────────────▼────────────────────────────────────────┐
│  MySQL 8 (单库)                                              │
│   users / invitation_codes / categories / tags / user_dicts │
│   pipeline_steps / upload_tasks / bills / bill_tags         │
│   ai_credentials / ai_strategies / monthly_incomes / assets │
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
| 鉴权 | JWT + bcrypt + 邀请码注册 | 简单稳定；邀请码控制扩张 |
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
├── tasks/        BackgroundTasks runner
├── bills/        列表/明细/手动改类/批量/重分类
├── reports/      yearly / monthly / category-summary / balance
├── assets/  incomes/
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
       ├─< monthly_incomes
       └─< assets
```

完整字段定义见 `migrations/versions/0001_initial_schema.py`，关键设计：

- `bills.bill_month`：MySQL 生成列 `DATE_FORMAT(bill_time, '%Y-%m')`，月度报表零成本聚合
- `bills` UNIQUE `(user_id, source, order_id)`：上传幂等
- `pipeline_steps.params` JSON：策略类型自定义参数，由 StrategyType 校验
- 所有用户级表 `user_id` 列建索引

---

## 6. 通用策略引擎

> **现状提醒**：截至当前迭代，代码中**仅实现了 `ai_classify` 一个策略类型**。后续候选类型（精确匹配、子串匹配、合并、扩散等）都没有写在代码里，仅作为未来候选保留在 [docs/strategy-types.md](./docs/strategy-types.md) 末尾。引擎本身（ABC + 注册器 + Pipeline runner）已具备完整扩展性，新增类型只需新增一个文件 + register 一行，前端按 `param_schema` 自动渲染。

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
upload CSV → parsers → list[BillItem]
           → engine.run(bill_items, user_pipeline_steps, ctx)
                 for step in steps (按 sort_order):
                     if step.enabled:
                         strategy = REGISTRY[step.strategy_type]
                         items = await strategy.run(items, step.params, ctx)
           → 持久化到 bills 表（含 classify_strategy_id / classify_strategy_type）
```

**为何 param_schema 是 JSONSchema**：前端拿到一份 schema 列表后能完全自动渲染策略实例的配置面板，新增策略类型 0 前端改动。

**MVP 仅内置 `ai_classify` 一种策略**。其他策略类型（精确匹配、子串匹配、合并、扩散等）将根据实际需求按需单独迭代。引擎本身已具备完整扩展性。详细见 [docs/strategy-types.md](./docs/strategy-types.md)。

---

## 7. AI 抽象层

```python
class LLMProvider(ABC):
    name: str          # openai / qwen / claude / gemini / glm / kimi
    async def classify(self, prompt: str, ctx: dict) -> ClassifyResult: ...
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
├── stores/                  Pinia: user / meta / pipeline / ai
├── api/                     axios 实例 + 模块化 client
├── views/                   与路由一一对应
├── components/              AppLayout / BillTable / PipelineEditor / ...
├── composables/             useAsyncState / useMonthRange / ...
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
