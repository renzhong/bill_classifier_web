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

echo "==> 同步后端代码与 compose 文件"
rsync -avz --delete \
  --exclude '__pycache__' --exclude '.venv' --exclude 'uploads' \
  backend/ "$TARGET:$REMOTE_DIR/backend/"
rsync -avz docker-compose.prod.yml docker/ .env.example "$TARGET:$REMOTE_DIR/"

echo "==> 远端构建并启动后端容器"
ssh "$TARGET" "cd $REMOTE_DIR && docker compose -f docker-compose.prod.yml up -d --build backend"

echo "==> 提醒：在宿主机 /etc/nginx/sites-enabled/ 放置 nginx/sites/bill-classifier.prod.conf 并 nginx -s reload"
echo "Done."
