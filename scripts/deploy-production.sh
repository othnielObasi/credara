#!/usr/bin/env bash
# Deploy Credara to production (Docker Compose + Caddy).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Missing .env at repo root. Copy .env.example and set production secrets."
  exit 1
fi

echo "Deploying Credara to production..."
echo "  Domain: credara.nov-tia.com (see infra/Caddyfile)"
echo ""

docker compose -f infra/docker-compose.yml build --pull
docker compose -f infra/docker-compose.yml up -d

echo ""
echo "Waiting for API health..."
for i in $(seq 1 30); do
  if curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1; then
    echo "API healthy."
    break
  fi
  sleep 2
done

if curl -sf http://127.0.0.1:3000/ >/dev/null 2>&1; then
  echo "Web healthy at http://127.0.0.1:3000/"
else
  echo "Web not responding yet — check: docker compose -f infra/docker-compose.yml logs web"
fi

echo ""
echo "Production deploy complete."
echo "  Public URL: https://credara.nov-tia.com/"
echo "  Logs:       docker compose -f infra/docker-compose.yml logs -f"
