SHELL := /bin/bash

.PHONY: dev dev-local deploy-production docker-setup test lint zip setup-env

setup-env:
	bash scripts/setup-env.sh

docker-setup:
	sudo apt-get update -qq
	sudo apt-get install -y docker.io docker-compose-v2
	sudo mkdir -p /etc/docker
	@echo '{"storage-driver":"vfs"}' | sudo tee /etc/docker/daemon.json
	sudo usermod -aG docker "$$USER" 2>/dev/null || true
	sudo pkill dockerd 2>/dev/null || true
	sleep 2
	sudo nohup dockerd >/tmp/dockerd.log 2>&1 &
	sleep 3
	bash scripts/ensure-docker.sh

dev:
	bash scripts/docker-dev.sh

dev-local:
	bash scripts/dev-local.sh

deploy-production:
	bash scripts/deploy-production.sh

test:
	cd apps/api && pytest -q
	cd contracts && npm test

lint:
	cd apps/api && ruff check app tests
	cd apps/web && npm run lint

zip:
	cd /mnt/data && zip -r credara-enterprise-codebase.zip credara-enterprise -x "*/node_modules/*" "*/.next/*" "*/__pycache__/*" "*/.venv/*"
