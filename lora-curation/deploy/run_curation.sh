#!/usr/bin/env bash
# Build prompts → Forge batch → start reviewer.
set -euo pipefail

CUR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LORA="$(cd "$CUR/.." && pwd)"
ROOT="$(cd "$LORA/.." && pwd)"
cd "$ROOT"

# shellcheck source=forge_user.sh
source "${CUR}/forge_user.sh"
export FORGE_DIR="${FORGE_DIR:-$(default_forge_dir)}"

PY="${PY:-python3}"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
fi

export FORGE_URL="${FORGE_URL:-http://127.0.0.1:7860}"
VARIANTS="${VARIANTS:-2}"
PORT="${PORT:-8765}"
SKIP_GENERATE="${SKIP_GENERATE:-0}"

echo "=== run_curation ==="
echo "FORGE_URL=$FORGE_URL  FORGE_DIR=$FORGE_DIR  variants=$VARIANTS  port=$PORT"

echo "[1/3] build_prompts…"
"$PY" "$LORA/build_prompts.py" --variants "$VARIANTS"

if [[ "$SKIP_GENERATE" != "1" ]]; then
  echo "[2/3] generate_batch (Forge)…"
  # wait for API
  for i in $(seq 1 60); do
    if curl -sf "$FORGE_URL/sdapi/v1/sd-models" >/dev/null 2>&1; then
      echo "Forge API ready"
      break
    fi
    if [[ "$i" -eq 60 ]]; then
      echo "Forge API not reachable at $FORGE_URL" >&2
      exit 1
    fi
    sleep 2
  done
  "$PY" "$LORA/generate_batch_gpu.py" --skip-existing --continue-on-error
else
  echo "[2/3] skip generate (SKIP_GENERATE=1)"
fi

echo "[3/3] reviewer http://0.0.0.0:${PORT}/"
exec "$PY" "$LORA/serve_reviewer.py" --host 0.0.0.0 --port "$PORT"
