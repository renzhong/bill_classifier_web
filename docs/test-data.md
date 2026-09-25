# 可复用测试数据

日常调试使用持久化 MySQL；需要回到相同起点时恢复 SQL 快照。
数据库容器只初始化一次，重启服务、切换分支或重新运行初始化都不会清空账单。
自动回归测试仍创建独立测试用户，结束时仅清理自身数据。

## 初始化和启动

需要 Docker、uv、Node.js。依赖保存在项目自己的 `.venv` 和 `node_modules`。

```sh
make testdata-init
# 首次使用前端时：cd frontend && npm ci
make testdata-backend   # 一个终端
make testdata-frontend  # 另一个终端
```

访问 <http://127.0.0.1:15173>，合成测试账号为 `demo@example.com` / `Demo-only-123456`。
这个账号仅用于本机测试。后端监听 `127.0.0.1:18000`。

固定数据库为 `127.0.0.1:33316/bcw_fixture_test`，容器名 `bcw-testdata-mysql`。
数据保存在 Docker 命名卷 `bcw-testdata-mysql-data`，不依赖某个 Git 工作树目录。
数据库连接配置、JWT / Fernet 密钥和 SQL 快照默认保存在：

```text
~/.local/share/bill-classifier-web/testdata/
  environment.env      # 随机生成的本机配置，权限 600
  baseline.sql         # 初始库结构和固定配置，可直接导入 MySQL
  snapshots/           # 后续手动快照，以及每次恢复前的自动备份
  uploads/
    wechat.xlsx / wechat.csv
    alipay.xlsx / alipay.csv
    expected.json      # 各条记录的金额和预期分类
```

这些本地文件不会进入 Git。SQL 快照可能包含以后上传的账单和加密 AI 凭据，均以权限 600 保存。
备份数据库时一并保留 `environment.env`，恢复加密凭据需要其中同一份 Fernet 密钥。
如需改变本地保存路径，在首次初始化前设置 `BCW_TESTDATA_DIR`，后续沿用该路径。

## 固定样本

数据源为 `backend/devdata/cases.json` 和 `seed.sql`，全部为合成数据。
初始化创建账号、餐饮 / 交通 / 购物三个类别、一份 AI 规则和一个默认禁用的分类步骤。
初始账单为空，适合测试完整上传流程。

每种来源有 6 条记录：正常餐饮、交通、购物、部分退款、无法判断的收入转账和带前导零的 65 位订单号。
样本中 5 条有旧 AI 参考类别、1 条无参考类别；本轮手动测试规则只会命中
“地铁乘车”一条。退款后金额为 70 元。
同一来源重复上传 CSV 或 Excel，账单总数应保持 6 条；分别上传微信和支付宝则共 12 条。
样本日期固定在 2026 年 1—2 月，查看报表时选择对应月份。

当前上传只解析为临时账单，不会调用 AI。要验证本轮交互，先在临时表格
查看解析结果，点击“开始分类”（固定名称正则“地铁|公交 → 交通”），
手动修正类别后点击“归档账单”。重复上传会去重。

若需验证保留的 AI Pipeline，可使用单条账单显式重分类接口。人工改类账单
不会交给 AI；这与当前上传流程独立。
默认数据不含真实 API key，不会自行调用付费模型。

自动测试使用同一份合成 SQL 和上传文件，验证临时解析、显式测试分类、
人工覆盖、归档、退款金额及去重。旧 AI Pipeline 的提示词和模型返回测试
仍由独立策略测试覆盖。

## 保存和恢复

```sh
make testdata-snapshot  # 保存当前状态，打印新 SQL 文件路径
make testdata-restore   # 恢复初始 baseline.sql；恢复前自动保存当前状态

# 恢复某个手动快照
python3 scripts/testdata.py restore --from-sql /absolute/path/snapshot.sql
```

恢复只作用于专用 `bcw_fixture_test` 库，会替换该库当前数据；不会连接原项目的数据库。
操作前先停止测试后端，恢复后再运行 `make testdata-backend`。
恢复后自动执行当前分支的数据库迁移；迁移不能降级，不要把更新分支的快照恢复给旧代码使用。

通常先配好类别、规则和 AI 凭据，保存一份自己的快照。以后调试失败时恢复这份快照，省去重复配置。
