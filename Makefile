.PHONY: dev test test-nginx down logs migrate revision lint backend-shell frontend-shell mysql-shell build-prod

COMPOSE := docker compose

dev:
	$(COMPOSE) up -d mysql backend frontend
	@echo "Backend  : http://localhost:$${BACKEND_HOST_PORT:-8000}/docs"
	@echo "Frontend : http://localhost:$${FRONTEND_HOST_PORT:-5173}"

test:
	$(COMPOSE) --profile test up -d
	@echo "Nginx联调 : http://localhost:$${NGINX_TEST_HOST_PORT:-8088}"

test-nginx:
	$(COMPOSE) --profile test up -d nginx

down:
	$(COMPOSE) --profile test down

logs:
	$(COMPOSE) logs -f --tail=200 backend frontend

migrate:
	$(COMPOSE) exec backend uv run alembic upgrade head

revision:
	@read -p "migration message: " msg; \
	$(COMPOSE) exec backend uv run alembic revision --autogenerate -m "$$msg"

lint:
	$(COMPOSE) exec backend uv run ruff check app tests
	$(COMPOSE) exec frontend npm run lint

backend-shell:
	$(COMPOSE) exec backend bash

frontend-shell:
	$(COMPOSE) exec frontend sh

mysql-shell:
	$(COMPOSE) exec mysql mysql -u$${MYSQL_USER:-bcw} -p$${MYSQL_PASSWORD:-bcw_dev_password} $${MYSQL_DATABASE:-bill_classifier_web}

build-prod:
	docker build -f docker/Dockerfile.backend -t bcw-backend:latest .
	cd frontend && npm ci && npm run build
	@echo "Frontend dist 已生成于 frontend/dist，请 rsync 至 prod 机器 /opt/bill-classifier-web/frontend/dist"
