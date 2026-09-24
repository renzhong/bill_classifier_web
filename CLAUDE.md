# CLAUDE.md — 项目开发约定

人与 AI 协作时共同遵守的开发指南。**进入本项目前请先读一遍。**

---

## 1. 项目快照

通用账单分类 Web 系统。Vue 3 + Naive UI 前端 + FastAPI + MySQL 后端。核心是「**用户在 Web 上配置策略 Pipeline，系统按 Pipeline 自动分类**」。详细架构见 [arch.md](./arch.md)。

---

## 2. 命令速查

| 用途 | 命令 |
|---|---|
| 起 dev 环境（mysql + backend + frontend） | `make dev` |
| 起测试环境（额外加 nginx 联调容器） | `make test` |
| 停服务 | `make down` |
| 看实时日志 | `make logs` |
| 执行 alembic upgrade head | `make migrate` |
| 新建一份 migration | `make revision` |
| 进入后端容器 shell | `make backend-shell` |
| 进入前端容器 shell | `make frontend-shell` |
| 进入 mysql shell | `make mysql-shell` |
| 后端 lint | `make lint`（或 `uv run ruff check app tests`） |
| 后端测试 | `uv run pytest`（容器内） |
| 前端构建 | `cd frontend && npm run build` |

---

## 3. 后端约定

### 3.1 分层

- `app/api/v1/` — 路由聚合
- `app/<module>/router.py` — 模块 HTTP 入口
- `app/<module>/service.py` — 业务逻辑（接收 session + 已校验的 schema）
- `app/schemas/<module>.py` — Pydantic 输入输出模型
- `app/models/<table>.py` — SQLAlchemy ORM
- `app/core/` — config / db / security / deps / logging（跨模块共用）

### 3.2 SQLAlchemy session

- 用 `app.core.deps.SessionDep` 注入异步 session
- service 函数自己 `await session.commit()`
- 长事务里多步操作时用 `await session.flush()` 拿自增主键
- 启用 `expire_on_commit=False`，commit 后仍能读对象字段

### 3.3 响应与错误

- 所有成功响应统一 `{code, msg, data}`（用 `app.core.response.ok()`）
- 错误抛 `HTTPException`，由 main.py 的全局 handler 转成 `{code, msg, data}`
- service 层不直接返回 dict，由 router 包装

### 3.4 密钥

- 写 DB 的敏感字段（AI api_key 等）必须 `encrypt_secret()`，读时 `decrypt_secret()`
- 永远不要把 JWT secret / Fernet key 写进代码或 commit
- `.env` 不提交，`.env.example` 维护变量名清单

### 3.5 添加新表

```bash
make backend-shell
uv run alembic revision -m "describe what"      # 手写 SQL
# 或 uv run alembic revision --autogenerate -m "..."
uv run alembic upgrade head
```

ORM 新模型务必在 `app/models/__init__.py` 中导出，否则 autogenerate 看不到。

---

## 4. 前端约定

### 4.1 组件命名

- `views/` 与路由一一对应，PascalCase
- `components/` 是可复用块，PascalCase
- `composables/use*.ts` 共用逻辑

### 4.2 状态

- Pinia store 只保存"跨页面共享 + 启动时拉一次"的数据（user / categories / tags / dicts / strategyTypes）
- 页面级数据不入 store，组件内 `ref` + `onMounted` 拉

### 4.3 API 调用

- 必须走 `src/api/request.ts`，不要在组件里直接 `axios.get`
- 每个模块一个 `src/api/<module>.ts`，导出强类型函数
- 后端返回的 `{code,msg,data}` 已被拦截器拆包，函数直接拿 `data`

### 4.4 表单/表格

- 优先用 Naive UI 组件（`n-form`、`n-data-table`、`n-upload` 等）
- 当前账单明细使用 `n-data-table` 和服务端分页；需要更大列表时再评估虚拟滚动

---

## 5. 扩展指南

### 5.1 新增 StrategyType

1. 在 `backend/app/classify/strategy_types/<name>.py` 实现 `StrategyType` ABC：
   ```python
   class MyStrategy(StrategyType):
       type_key = "my_type"
       display_name = "我的策略"
       description = "..."
       param_schema = {...}      # JSONSchema 形式

       def validate_params(self, params): ...
       async def run(self, items, params, ctx): ...
   ```
2. 在 `backend/app/classify/strategy_types/__init__.py` 顶部 `import` 并调用 `register(MyStrategy())`（`register` 来自 `strategy_types/registry.py`）
3. 在 `backend/tests/classify/test_<name>.py` 写单测（参考 `test_ai_classify.py` 用 FakeSession 模式）
4. 检查 `frontend/src/components/StrategyParamForm.vue` 是否支持新参数类型；当前只处理数字、布尔值和 `strategy_id` 特例

### 5.2 新增 AI Provider

1. 在 `backend/app/ai/providers/<name>.py` 继承 `LLMProvider`，实现 `async def chat(*, prompt, model, api_key, base_url) -> str`
2. 在 `backend/app/ai/registry.py` 顶部 import 并加入 `PROVIDERS` 字典（循环里 `_register(...)`）
3. 如果是 OpenAI 兼容协议（base_url + model_name + key），优先继承 `openai_compat._OpenAICompatBase`，仅覆盖 `provider_key` / `default_base_url` / `suggested_models` 三个属性

---

## 6. 测试约定

- 后端：pytest + pytest-asyncio，覆盖解析器、分类、安全与 MySQL 上传任务；具体用例以 `backend/tests/` 和 CI 为准
- 新增 StrategyType / Provider 时务必补一份单测，纯 in-memory 跑（不连 DB、不连真 LLM）
- 前端：MVP 阶段没有引入 vitest / Playwright，依赖 `uv run pytest` + 类型检查保证后端正确，前端靠人工点点确认
- 测试数据：用最小化、无业务含义的 fixture；不复用任何个人账单

---

## 7. 提交与分支

- 主分支：`main`
- 编码任务的功能分支使用 `codex/<scope>` 前缀
- Commit message：祈使语气，主题行 ≤ 50 字符、首字母大写，正文 72 字符折行（why 为主，不写 how）
- 主题与正文之间空一行

---

## 8. 部署 checklist

- [ ] `.env` 在生产机上正确填写（特别是 JWT / Fernet）
- [ ] MySQL 实例已建库并赋权
- [ ] alembic 已 `upgrade head`
- [ ] 用 `seed_admin` 创建首个管理员
- [ ] 前端 dist 已 rsync 到 `/opt/bill-classifier-web/frontend/dist/`
- [ ] 后端容器已起，`/healthz` 通
- [ ] 宿主 nginx 配置已 `nginx -t` 通过并 reload
- [ ] HTTPS 证书路径正确，自动续期已配置
