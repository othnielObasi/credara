SHELL := /bin/bash

.PHONY: dev dev-local test lint zip setup-env

setup-env:
	bash scripts/setup-env.sh

dev:
	docker compose -f infra/docker-compose.yml up --build

dev-local:
	bash scripts/dev-local.sh

test:
	cd apps/api && pytest -q
	cd contracts && npm test

lint:
	cd apps/api && ruff check app tests
	cd apps/web && npm run lint

zip:
	cd /mnt/data && zip -r credara-enterprise-codebase.zip credara-enterprise -x "*/node_modules/*" "*/.next/*" "*/__pycache__/*" "*/.venv/*"
