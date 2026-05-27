# PRD 01 · 账号与邀请码

## 用户故事
- 作为新用户，我需要用一条邀请码注册账号
- 作为管理员，我能签发与撤销邀请码、查看使用情况
- 作为已注册用户，我能登录后获得 JWT，使用全站功能

## 页面
- `/register`：邮箱 + 昵称（可选） + 密码 + 邀请码
- `/login`：邮箱 + 密码
- 设置页 → 邀请码管理（仅管理员可见）

## API
- `POST /api/v1/auth/register`：校验邀请码，创建用户，邀请码 used_count+1
- `POST /api/v1/auth/login`：返回 access + refresh token
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`
- `GET /api/v1/auth/invitations`（admin）
- `POST /api/v1/auth/invitations`（admin）

## 数据模型
- `users(id, email UNIQUE, password_hash, nickname, status, is_admin, ts)`
- `invitation_codes(id, code UNIQUE, created_by, used_by, used_at, expires_at, max_uses, used_count, ts)`

## 验收
- 邀请码错误 → 注册失败提示
- 同邮箱重复注册 → 失败
- 邀请码达上限或过期 → 失败
- 登录后 JWT 通过 `/auth/me` 验证有效
- 非 admin 调 `/invitations` 返回 403

## 不做
- 邮箱验证码（MVP 信任邀请码就足够）
- OAuth 第三方登录
