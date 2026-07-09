#!/usr/bin/env bash
# Start Credara locally without Docker (API + Next.js web).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Missing .env — run: make setup-env"
  exit 1
fi

mkdir -p apps/api
ln -sf ../../.env apps/api/.env

if [[ -z "${DATABASE_URL:-}" ]] || [[ "${DATABASE_URL}" == postgresql* ]]; then
  export DATABASE_URL="sqlite:///${ROOT}/apps/api/credara.db"
fi

API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-3000}"

echo ""
echo "Credara — SME trade finance on Polygon"
echo "  Open:  http://localhost:${WEB_PORT}/"
echo "  API:   http://localhost:${API_PORT}/docs"
echo ""
echo "This is the Credara React app. The old HTML demo is archived (not used)."
echo ""

run_api() {
  cd "$ROOT/apps/api"
  export DATABASE_URL
  if command -v uvicorn >/dev/null 2>&1; then
    exec uvicorn app.main:app --host 0.0.0.0 --port "$API_PORT" --reload
  else
    exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port "$API_PORT" --reload
  fi
}

run_web() {
  cd "$ROOT/apps/web"
  if command -v pnpm >/dev/null 2>&1; then
    exec pnpm dev --port "$WEB_PORT"
  else
    exec npm run dev -- --port "$WEB_PORT"
  fi
}

case "${1:-}" in
  api) run_api ;;
  web) run_web ;;
  *)
    echo "Run in two terminals:"
    echo "  Terminal 1: bash scripts/dev-local.sh api"
    echo "  Terminal 2: bash scripts/dev-local.sh web"
    echo ""
    echo "Or with Docker: make dev"
    ;;
esac
