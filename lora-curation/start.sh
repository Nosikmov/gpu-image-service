#!/usr/bin/env bash
# LoRA curation: prompts + GPU batch (optional) + web reviewer.
set -euo pipefail
CUR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$CUR/.." && pwd)"
cd "$ROOT"

PORT="${PORT:-8765}"
PY="${PY:-python3}"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
fi

echo "=== LoRA curation (gpu-image-service) ==="
echo "root: $ROOT"
echo "python: $PY"

if [[ ! -f "$CUR/prompts.json" ]]; then
  echo "[1/3] prompts.json — создаю…"
  "$PY" "$CUR/build_prompts.py"
else
  echo "[1/3] prompts.json — OK"
fi

IMG_COUNT=$(find "$CUR/images" -maxdepth 1 -type f \( -name '*.png' -o -name '*.webp' -o -name '*.jpg' \) 2>/dev/null | wc -l)
echo "[2/3] картинок в images/: $IMG_COUNT / 100"

if [[ "$IMG_COUNT" -eq 0 ]]; then
  echo "    Сгенерировать через Comfy relay:"
  echo "    $PY $CUR/generate_batch_gpu.py --skip-existing --continue-on-error"
fi

echo "[3/3] Веб-оценка на http://127.0.0.1:${PORT}/"
echo "     A=approve  R=reject  M=maybe"
exec "$PY" "$CUR/serve_reviewer.py" --host 0.0.0.0 --port "$PORT"
