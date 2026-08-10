#!/usr/bin/env bash
# Example: place SDXL base into the models volume (download yourself; large file).
# Usage: MODEL_URL=https://... ./scripts/fetch-model.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
if [[ -f "$ROOT/.env" ]]; then set -a; source "$ROOT/.env"; set +a; fi
DEST_DIR="${MODELS_PATH:-$ROOT/data/models}/checkpoints"
mkdir -p "$DEST_DIR"
NAME="${DEFAULT_MODEL:-sd_xl_base_1.0.safetensors}"
if [[ -z "${MODEL_URL:-}" ]]; then
  echo "Set MODEL_URL to a direct download URL for $NAME"
  echo "Example (Hugging Face requires token for gated models):"
  echo "  MODEL_URL=https://huggingface.co/.../resolve/main/$NAME ./scripts/fetch-model.sh"
  exit 1
fi
echo "Downloading to $DEST_DIR/$NAME"
curl -fL --progress-bar -o "$DEST_DIR/$NAME" "$MODEL_URL"
ls -lh "$DEST_DIR/$NAME"
