# 测试

需要长期保留账单、重复上传 Excel 或比较分类结果时，使用[固定测试数据与 SQL 快照](test-data.md)。

依赖仅安装到 `backend/.venv` 和 `frontend/node_modules`。测试全部使用合成数据，不需要真实账单或 AI API key。

## 单元测试与前端构建

在 `backend/` 执行：

```sh
uv sync --frozen
uv run --frozen ruff check app tests
uv run --frozen python -m pytest -q
```

在 `frontend/` 执行：

```sh
npm ci
npm run build
```

## MySQL 集成测试

先准备独立、可丢弃的 MySQL 8 数据库。库名必须以 `_test` 结尾；不得连接开发或生产账单库。
在 `backend/` 中设置测试库连接信息后执行：

```sh
export BCW_DB_HOST=127.0.0.1
export BCW_DB_PORT=3306
export BCW_DB_NAME=bcw_test
export BCW_DB_USER=bcw
export BCW_DB_PASSWORD=bcw_test
export BCW_TEST_MYSQL=1
uv run --frozen alembic upgrade head
uv run --frozen python -m pytest -q
```

未设置 `BCW_TEST_MYSQL=1` 时，MySQL 集成测试会明确跳过。集成测试覆盖：

- 重复或超长账单跳过后，前后的正常账单仍能保存。
- 65 位订单号入库、异常事务和分类失败的任务状态。
- 账号登录、初始空配置加载、XLSX 上传、重复上传与账单查询。
- 固定 SQL 数据集上的微信 / 支付宝 CSV 和 XLSX 分类流程（模拟模型回复）、退款金额和重复上传去重。

GitHub Actions 的 CI 使用临时 MySQL 执行这些检查，并独立构建前端。
