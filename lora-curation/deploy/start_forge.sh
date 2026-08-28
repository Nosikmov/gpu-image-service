#!/usr/bin/env bash
# Start Forge WebUI with API for curation (run inside tmux).
set -euo pipefail

FORGE="${FORGE_DIR:-${FORGE:-${HOME}/stable-diffusion-webui-forge}}"

if [[ ! -f "${FORGE}/webui.sh" ]]; then
  echo "Forge not found: ${FORGE}" >&2
  echo "Run: bash lora-curation/deploy/setup_server.sh" >&2
  exit 1
fi

export FORGE_DIR="${FORGE}"
cd "${FORGE}"
echo "=== Forge @ ${FORGE} ==="
echo "API: http://127.0.0.1:7860"
echo "Set Diffusion in Low Bits: Automatic (fp16 LoRA)"
exec ./webui.sh
