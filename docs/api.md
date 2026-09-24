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
| POST | /bills/upload | multipart：CSV/XLSX file + source + owner_label + tag_ids；每笔新账单继承标签，仅解析为临时账单 |
| GET | /bills | 仅归档账单；filter: month/source/category_id/unclassified/tag_id/keyword/lifecycle/report_expense/page；`report_expense=true` 仅返回计入分类汇总的支出 |
| GET PATCH | /bills/{id} | 详情 / 手工改类（`category_id` 可显式为 null）；来源平台和上传标签不可修改 |
| POST | /bills/{id}/reclassify | 单条重跑 Pipeline |
| POST | /bills/batch | 兼容旧接口的 set_category / delete；add_tag / remove_tag 返回 400 |
| GET | /upload-tasks[/{id}] | 上传任务列表 / 详情，含逐行 `parse_errors` |
| GET | /upload-tasks/{id}/bills | 查询本批次临时或归档账单，分页 |
| POST | /upload-tasks/{id}/classify | 仅运行固定名称正则测试规则“地铁\|公交 → 交通”，跳过人工改类 |
| POST | /upload-tasks/{id}/archive | 原子归档整个批次，可重复调用 |

上传任务状态为 `pending → parsing → parsed → classified → archived`，解析异常为 `failed`。
用户可以在 `parsed` 或 `classified` 状态归档。只有 `archived` 账单进入报表。

### assets / investments / incomes
| Method | Path | 说明 |
|---|---|---|
| GET POST | /asset-items | 可复用的命名资产项、负债项 |
| PATCH | /asset-items/{id} | 改名或停用，历史月金额不丢失 |
| GET | /asset-months/{month} | 本月各项金额（未填为 null）、投资估值、资产/负债/净资产及完整状态 |
| PUT | /asset-items/{id}/months/{month} | 填写本月金额，0 与未填写不同 |
| GET POST | /investments | 投资项及初始本金；可选 `linked_asset_item_id` 关联已有资产项防重复计入 |
| PATCH | /investments/{id} | 改名、改本金、修改关联资产项或停用 |
| GET | /investments/months/{month} | 月买卖、现值和盈亏；缺估值时盈亏为 null |
| PUT | /investments/{id}/months/{month} | 填写本月买卖与月末现值 |
| GET POST | /income-entries | 逐笔收入，可按 month/year 查询，同月同来源允许多笔 |
| PATCH DELETE | /income-entries/{id} | 编辑 / 删除逐笔收入 |
| GET | /income-summary?year=&month= | 月收入、年收入及该月旧月度记录 |
| GET | /assets | 只读查看旧月度资产快照；已迁入可复用项目，后续填写使用 `/asset-items` |
| GET POST PATCH DELETE | /incomes 旧接口 | 兼容旧月度收入记录；与逐笔收入一起汇总，但不伪造具体日期 |

### reports
| Method | Path | 说明 |
|---|---|---|
| GET | /reports/yearly?year=2026 | 每月账单 income / expense / balance（收支差额）+ 年度合计，不含另行录入的收入 |
| GET | /reports/monthly?month=2026-05 | 已归档账单收支、录入收入、资产、负债、净资产与净资产较上月变化 |
| GET | /reports/category-summary?month=2026-05 | 按类别支出汇总 + 占比 |
| GET | /reports/balance?month=2026-05 | 手工资产与投资估值按来源类型汇总，不包含负债 |

## 错误码

- 0：成功
- 4xx：HTTP 状态码原值；`msg` 含具体原因
- 业务逻辑非法走 400（如类别名重复、规则参数错误）
- 鉴权失败走 401，权限不足走 403
