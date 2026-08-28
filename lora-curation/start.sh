#!/usr/bin/env bash
# LoRA curation: prompts + Forge batch hint + web reviewer.
set -euo pipefail
CUR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$CUR/.." && pwd)"
cd "$ROOT"

PORT="${PORT:-8765}"
FORGE_URL="${FORGE_URL:-http://127.0.0.1:7860}"
PY="${PY:-python3}"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
fi

echo "=== LoRA curation (Forge Flux Q6_K / gameFarmling) ==="
echo "root: $ROOT"
echo "python: $PY"
echo "FORGE_URL: $FORGE_URL"

if [[ ! -f "$CUR/prompts.json" ]]; then
  echo "[1/3] prompts.json — создаю…"
  "$PY" "$CUR/build_prompts.py" --variants "${VARIANTS:-2}"
else
  echo "[1/3] prompts.json — OK"
fi

IMG_COUNT=$(find "$CUR/images" -maxdepth 1 -type f \( -name '*.png' -o -name '*.webp' -o -name '*.jpg' \) 2>/dev/null | wc -l | tr -d ' ')
BASE_COUNT=$( "$PY" -c "import json; print(json.load(open('$CUR/prompts.json',encoding='utf-8'))['count'])" 2>/dev/null || echo "?" )
echo "[2/3] картинок в images/: $IMG_COUNT / $BASE_COUNT"

if [[ "$IMG_COUNT" -eq 0 ]]; then
  echo "    Сгенерировать через Forge API:"
  echo "    FORGE_URL=$FORGE_URL $PY $CUR/generate_batch_gpu.py --skip-existing --continue-on-error"
fi

echo "[3/3] Веб-оценка на http://127.0.0.1:${PORT}/"
echo "     A=approve  R=reject  M=maybe"
exec "$PY" "$CUR/serve_reviewer.py" --host 0.0.0.0 --port "$PORT"
