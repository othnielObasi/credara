#!/usr/bin/env bash
# Create .env from .env.example (if missing) and link it for apps/api.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  echo "✓ .env already exists at $ROOT/.env"
else
  cp .env.example .env
  echo "✓ Created .env from .env.example"
  echo "  → Edit .env and add your real secrets (Polygon keys, JWT_SECRET, etc.)"
fi

mkdir -p apps/api
ln -sf ../../.env apps/api/.env
echo "✓ Linked apps/api/.env → ../../.env"

echo ""
echo "Next steps:"
echo "  1. Open .env in the repo root and fill in your values"
echo "  2. Required for Polygon demo: RELAYER_PRIVATE_KEY, PROOF_REGISTRY_ADDRESS, POLYGON_RPC_URL"
echo "  3. Start stack: make dev"
