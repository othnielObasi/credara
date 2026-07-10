#!/usr/bin/env bash
# Run full Credara stack with Docker Compose.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# shellcheck source=scripts/ensure-docker.sh
source "$ROOT/scripts/ensure-docker.sh"

if [[ ! -f .env ]]; then
  make setup-env
fi

$DOCKER compose -f infra/docker-compose.yml up --build "$@"
