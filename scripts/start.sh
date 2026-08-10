#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Missing .env — run ./scripts/install.sh first"
  exit 1
fi

# shellcheck disable=SC1091
set -a
source .env
set +a

docker compose up -d --build
docker compose ps
echo "API: http://127.0.0.1:${API_PORT:-8080}/health"
