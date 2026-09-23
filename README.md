# Bill Classifier Web

通用账单分类 Web 系统。上传支付宝 / 微信账单 CSV，按用户在 Web 上编排的「策略 Pipeline」自动归类到用户自定义的业务分类，并提供报表、资产与收入管理页面。

**通用配置驱动**：系统提供 `StrategyType` 扩展骨架（ABC + 注册器 + Pipeline runner）；**当前迭代仅内置 `ai_classify` 一种策略**——把用户填写的多条文本规则注入 prompt template，逐条账单调 LLM 分类。支持 6 个 LLM provider（openai / qwen / glm / kimi / claude / gemini）。其他策略类型（精确匹配 / 合并 / 时间窗扩散等）按需后续单独迭代，新增只需加一个文件 + register 一行，前端无需改动。

所有类别、tag、字典、AI 凭据、AI prompt 文本、Pipeline 顺序——全部由用户在 Web 界面创建，代码 0 业务数据。

---

## 快速开始（本地开发）

依赖：Docker / Docker Compose / make

```bash
cp .env.example .env
# 至少修改：BCW_JWT_SECRET、BCW_FERNET_KEY（用下面命令生成 Fernet key）
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

make dev                   # 起 mysql + backend + frontend（backend 容器启动时会自动跑 alembic upgrade head）

# 等 backend 容器 healthy 后，创建管理员 + 邀请码
docker compose exec backend uv run python -m app.cli.seed_admin \
  --email admin@example.com --password yourpassword --invitations 3

# 后续新增 migration 后手动 upgrade
# make migrate
```

访问：

- 前端：http://localhost:5173
- 后端文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/healthz

用打印出来的邀请码访问 `/register` 注册第二个用户，或用 admin 账号直接登录。

### 联调环境（容器版 nginx 反代）

```bash
make test                  # 起 nginx 容器，反代 backend 与 frontend
# 访问 http://localhost:8088
```

---

## 目录速览

```
backend/        FastAPI + SQLAlchemy 2.0 + Alembic + uv
frontend/       Vue 3 + Vite + Naive UI + Pinia
docker/         Dockerfile.backend / Dockerfile.frontend / mysql 初始化
nginx/          nginx.conf + sites/*.conf（dev / static / prod 三套）
prd/            按模块拆分的需求文档
docs/           策略类型、CSV parser、API 详解
arch.md         架构方案
CLAUDE.md       项目开发约定（人 + AI 共同遵守）
```

详细模块/数据库设计 → [arch.md](./arch.md)
详细开发约定 → [CLAUDE.md](./CLAUDE.md)

---

## 环境变量

见 `.env.example`。关键项：

| 变量 | 含义 |
|---|---|
| `BCW_JWT_SECRET` | JWT 签名密钥（必须改） |
| `BCW_FERNET_KEY` | AI api_key 落库加密密钥（必须改，用 Fernet 生成） |
| `BCW_DB_*` | MySQL 连接 |
| `BCW_CORS_ORIGINS` | 前端来源白名单，逗号分隔 |
| `BCW_UPLOAD_MAX_BYTES` | 上传账单最大字节 |

---

## 生产部署（极简）

参考 `deploy.sh`：

1. 本机 `npm run build` 构建前端
2. `rsync frontend/dist/` → 目标机 `/opt/bill-classifier-web/frontend/dist/`
3. 目标机 `docker compose -f docker-compose.prod.yml up -d --build backend`
4. 目标机 nginx 放置 `nginx/sites/bill-classifier.prod.conf`，`nginx -s reload`

---

## 文档索引

- [docs/test-data.md](./docs/test-data.md) — 持久化测试库、固定 Excel 样本和 SQL 快照恢复

- [arch.md](./arch.md) — 架构方案
- [CLAUDE.md](./CLAUDE.md) — 项目开发约定
- [prd/](./prd/) — 按模块拆分的需求文档
- [docs/strategy-types.md](./docs/strategy-types.md) — 内置策略类型清单
- [docs/parser-spec.md](./docs/parser-spec.md) — 账单 CSV 字段约定
- [docs/api.md](./docs/api.md) — API 总览
