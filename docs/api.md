# API 总览

完整交互文档：访问 `http://localhost:8000/docs`（FastAPI 自动生成 OpenAPI）。

## 全局约定
- Base URL：`/api/v1`
- 认证：`Authorization: Bearer <access_token>`
- 响应包络：`{code: 0|非0, msg: string, data: any}`
- 分页：`page` (1-based) + `page_size`

## 端点分组

### auth
| Method | Path | 权限 |
|---|---|---|
| POST | /auth/register | 公共（需邀请码） |
| POST | /auth/login | 公共 |
| POST | /auth/refresh | 公共 |
| GET | /auth/me | 登录 |
| GET | /auth/invitations | admin |
| POST | /auth/invitations | admin |
| POST | /auth/invitations/{id}/revoke | admin，撤销后不能注册 |

### categories / tags / dicts
| Method | Path | 说明 |
|---|---|---|
| GET POST | /categories | 列表 / 新建 |
| PATCH DELETE | /categories/{id} | 修改 / 删除（受引用保护） |
| POST | /categories/reorder | 批量改 sort_order |
| GET POST DELETE | /tags[/{id}] | tag CRUD |
| GET POST PATCH DELETE | /dicts[/{id}] | 字典 CRUD |
| GET POST | /dicts/{id}/entries | 字典条目列表 / 新建 |
| DELETE | /dicts/{id}/entries/{entry_id} | 删除条目 |
| POST | /dicts/{id}/entries/bulk | CSV 粘贴批量导入（fail-closed） |

### pipeline
| Method | Path | 说明 |
|---|---|---|
| GET | /pipeline/strategy-types | 列出所有已注册的 StrategyType + param_schema |
| GET POST | /pipeline/steps | 当前用户的 pipeline 步骤 |
| PATCH DELETE | /pipeline/steps/{id} | 修改 / 删除 |
| POST | /pipeline/steps/reorder | 批量改 sort_order |

### ai
| Method | Path | 说明 |
|---|---|---|
| GET | /ai/providers | 6 个内置 provider 元数据 |
| GET POST | /ai/credentials | 凭据（api_key Fernet 加密落库） |
| PATCH DELETE | /ai/credentials/{id} | 修改 / 删除（删除会解绑相关 strategy） |
| GET POST | /ai/strategies | AI 策略（含 strategy_text） |
| PATCH DELETE | /ai/strategies/{id} | 修改 / 删除 |
| POST | /ai/strategies/preview | 给定 strategy_text 渲染最终 prompt（前端预览用） |
| POST | /ai/test | 给样例账单跑一次分类（含或不含 strategy） |

### bills / upload-tasks
| Method | Path | 说明 |
|---|---|---|
| POST | /bills/upload | multipart：CSV/XLSX file + source + owner_label + tag_ids；每笔新账单继承标签 |
| GET | /bills | filter: month/source/category_id/tag_id/keyword/lifecycle/page |
| GET PATCH | /bills/{id} | 详情 / 手工改类（manual_overridden）/ 修改账单标签 |
| POST | /bills/{id}/reclassify | 单条重跑 Pipeline |
| POST | /bills/batch | set_category / add_tag / remove_tag / delete |
| GET | /upload-tasks[/{id}] | 上传任务列表 / 详情 |

### assets / incomes
| Method | Path | 说明 |
|---|---|---|
| GET POST | /assets | 资产快照 CRUD（?month=YYYY-MM 过滤） |
| PATCH DELETE | /assets/{id} | 修改 / 删除 |
| POST | /assets/copy | 从某月复制资产快照到目标月（overwrite 可选） |
| GET POST | /incomes | 月度收入 CRUD（?year= / ?month= 过滤） |
| PATCH DELETE | /incomes/{id} | 修改 / 删除 |

### reports
| Method | Path | 说明 |
|---|---|---|
| GET | /reports/yearly?year=2026 | 每月账单 income / expense / balance（收支差额）+ 年度合计，不含另行录入的收入 |
| GET | /reports/monthly?month=2026-05 | 账单支出、账单收入、录入收入、资产合计、资产较上月变化 |
| GET | /reports/category-summary?month=2026-05 | 按类别支出汇总 + 占比 |
| GET | /reports/balance?month=2026-05 | 资产按 asset_type 汇总 |

## 错误码

- 0：成功
- 4xx：HTTP 状态码原值；`msg` 含具体原因
- 业务逻辑非法走 400（如类别名重复、规则参数错误）
- 鉴权失败走 401，权限不足走 403
