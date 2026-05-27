#!/usr/bin/env bash
# 极简部署脚本：构建后端镜像 → 上线，前端 rsync 静态产物到目标机
# 用法: ./deploy.sh [user@host] [/opt/bill-classifier-web]
set -euo pipefail

TARGET="${1:-}"
REMOTE_DIR="${2:-/opt/bill-classifier-web}"

if [[ -z "$TARGET" ]]; then
  echo "Usage: $0 user@host [remote_dir]"
  exit 1
fi

echo "==> 构建前端"
( cd frontend && npm ci && npm run build )

echo "==> 同步前端 dist 至 $TARGET:$REMOTE_DIR/frontend/dist"
ssh "$TARGET" "mkdir -p $REMOTE_DIR/frontend"
rsync -avz --delete frontend/dist/ "$TARGET:$REMOTE_DIR/frontend/dist/"

echo "==> 同步后端代码"
rsync -avz --delete \
  --exclude '__pycache__' --exclude '.venv' --exclude 'uploads' --exclude '*.pyc' \
  backend/ "$TARGET:$REMOTE_DIR/backend/"

echo "==> 同步 docker / nginx / compose"
rsync -avz docker-compose.prod.yml .dockerignore .env.example "$TARGET:$REMOTE_DIR/"
rsync -avz --delete docker/ "$TARGET:$REMOTE_DIR/docker/"
rsync -avz --delete nginx/ "$TARGET:$REMOTE_DIR/nginx/"

echo "==> 远端构建并启动后端容器"
ssh "$TARGET" "cd $REMOTE_DIR && docker compose -f docker-compose.prod.yml up -d --build backend"

cat <<'NOTE'

==> 下一步（首次部署在远端执行）：
  1. 编辑 .env，至少配置 BCW_JWT_SECRET 与 BCW_FERNET_KEY；
  2. 进入 backend 容器创建首个管理员：
       docker compose -f docker-compose.prod.yml exec backend \
         uv run python -m app.cli.seed_admin --email you@example.com --password xxxxxx
  3. 把 nginx/sites/bill-classifier.prod.conf 拷至 /etc/nginx/sites-enabled/，
     修改 server_name / ssl_certificate 路径，nginx -t && nginx -s reload。
==> Done.
NOTE
