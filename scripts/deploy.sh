#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> deploy (models & generated volumes preserved)"
git pull --ff-only
docker compose build
docker compose up -d
docker compose ps
echo "Deploy complete."
