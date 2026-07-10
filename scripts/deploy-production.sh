#!/usr/bin/env bash
# Deploy Credara with Docker Compose (works in cloud workspace + production server).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# shellcheck source=scripts/ensure-docker.sh
source "$ROOT/scripts/ensure-docker.sh"

COMPOSE="$DOCKER compose -f infra/docker-compose.yml"

if [[ ! -f .env ]]; then
  echo "Missing .env at repo root. Run: make setup-env"
  exit 1
fi

echo "Deploying Credara..."
echo "  Web:  http://localhost:3000/"
echo "  API:  http://localhost:8000/health"
echo ""

$COMPOSE build --pull
$COMPOSE up -d

echo ""
echo "Waiting for API health..."
for _ in $(seq 1 45); do
  if curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1; then
    echo "API healthy."
    break
  fi
  sleep 2
done

if curl -sf http://127.0.0.1:3000/ >/dev/null 2>&1; then
  echo "Web healthy at http://localhost:3000/"
else
  echo "Web not responding yet — check: $COMPOSE logs web"
fi

echo ""
echo "Deploy complete."
echo "  Logs: $COMPOSE logs -f"
