# API 总览

完整交互文档：访问 `http://localhost:8000/docs`（FastAPI 自动生成 OpenAPI）。

## 全局约定
- Base URL：`/api/v1`
- 认证：`Authorization: Bearer <access_token>`
- 响应包络：`{code: 0|非0, msg: string, data: any}`
- 分页：`page` (1-based) + `page_size`

## 端点分组（M1 仅 auth；后续 milestone 逐步补全）

### auth
| Method | Path | 权限 |
|---|---|---|
| POST | /auth/register | 公共（需邀请码） |
| POST | /auth/login | 公共 |
| POST | /auth/refresh | 公共 |
| GET | /auth/me | 登录 |
| GET | /auth/invitations | admin |
| POST | /auth/invitations | admin |

### bills / categories / tags / dicts / pipeline / ai / reports / assets / incomes
M2-M5 实现，详见对应 PRD。
