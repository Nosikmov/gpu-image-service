#!/usr/bin/env bash
# Start Forge WebUI with API for curation (run inside tmux).
set -euo pipefail

DEPLOY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=forge_user.sh
source "${DEPLOY}/forge_user.sh"

FORGE="${FORGE_DIR:-${FORGE:-$(default_forge_dir)}}"

if [[ ! -f "${FORGE}/webui.sh" ]]; then
  echo "Forge not found: ${FORGE}" >&2
  echo "Run: bash lora-curation/deploy/setup_server.sh" >&2
  exit 1
fi

echo "=== Forge @ ${FORGE} ==="
if [[ "$(id -u)" -eq 0 ]]; then
  echo "Running as user: ${FORGE_USER} (Forge cannot start as root)"
fi
echo "API: http://127.0.0.1:7860"
echo "Set Diffusion in Low Bits: Automatic (fp16 LoRA)"

run_as_forge_user "${FORGE}" bash -lc "cd '${FORGE}' && ./webui.sh"
