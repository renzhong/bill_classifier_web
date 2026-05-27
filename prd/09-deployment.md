# PRD 09 · 部署

## 三环境

| 环境 | 前端 | 后端 | DB | nginx |
|---|---|---|---|---|
| dev | vite dev :5173 | uvicorn :8000 容器 reload | mysql 容器 | vite proxy |
| test | vite 容器 | uvicorn 容器 | mysql 容器 | nginx 容器 :8088 |
| prod | 宿主静态 dist | uvicorn 容器 :127.0.0.1:8080 | 宿主/RDS | 宿主 nginx :443 |

## 文件
- `docker-compose.yml`：dev 默认起 mysql/backend/frontend；`--profile test` 加 nginx 联调
- `docker-compose.prod.yml`：仅 backend
- `docker/Dockerfile.backend`：多阶段 base→dev/builder→runtime
- `docker/Dockerfile.frontend`：多阶段 builder（node:22）→ runtime（nginx:alpine，测试环境用）
- `nginx/nginx.conf` + `nginx/sites/{dev,static,prod}.conf`：参考 aliyun-config 的 sites/* 模式
- `deploy.sh`：本机 build + rsync + 远端 compose up

## 上线流程
1. 本机 `.env` 验证 OK
2. `cd frontend && npm run build`
3. `./deploy.sh user@host /opt/bill-classifier-web`
4. 远端机器准备：
   - `nginx/sites/bill-classifier.prod.conf` 拷到 `/etc/nginx/sites-enabled/` 并改 server_name + 证书路径
   - `/etc/nginx/ssl/` 放 SSL 证书
   - `nginx -t && nginx -s reload`
   - 容器 health check 通后访问

## 验收
- prod nginx 配置 `nginx -t` 通过
- HTTPS 访问主域名能加载前端
- 前端 `/api/auth/login` 走 nginx 反代到后端
- 后端 `/healthz` 通过 nginx 暴露
- SPA 路由刷新无 404（try_files 兜底）

## 不做
- CI/CD 流水线（MVP 手动 deploy.sh）
- 多机部署 / 负载均衡
- 日志聚合（先看容器 stdout）
