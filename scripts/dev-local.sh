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

set -a
# shellcheck disable=SC1091
source .env
set +a

API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-3000}"

use_sqlite() {
  export DATABASE_URL="sqlite:///${ROOT}/apps/api/credara.db"
  echo "Using SQLite: $DATABASE_URL"
}

if [[ "${CREDARA_USE_SQLITE:-}" == "1" ]]; then
  use_sqlite
elif [[ "${DATABASE_URL:-}" == postgresql* ]]; then
  if ! command -v pg_isready >/dev/null 2>&1 || ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo "Postgres not reachable — falling back to SQLite for local dev."
    use_sqlite
  fi
elif [[ -z "${DATABASE_URL:-}" ]]; then
  use_sqlite
fi

echo ""
echo "Credara — SME trade finance on Polygon"
echo "  Open:  http://localhost:${WEB_PORT}/"
echo "  API:   http://localhost:${API_PORT}/health"
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
  export API_PROXY_TARGET="${API_PROXY_TARGET:-http://localhost:${API_PORT}}"
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
    echo "Force SQLite: CREDARA_USE_SQLITE=1 bash scripts/dev-local.sh api"
    echo "With Docker:  make dev"
    ;;
esac
