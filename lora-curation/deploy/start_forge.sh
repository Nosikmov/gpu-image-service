#!/usr/bin/env bash
# Start Forge WebUI with API for curation (run inside tmux).
set -euo pipefail

DEPLOY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=forge_user.sh
source "${DEPLOY}/forge_user.sh"

FORGE="${FORGE_DIR:-${FORGE:-$(default_forge_dir)}}"

if [[ ! -f "${FORGE}/webui.sh" ]]; then
  echo "Forge not found: ${FORGE}" >&2
  echo "Run: ./cycle.sh setup-forge" >&2
  exit 1
fi

echo "=== Forge @ ${FORGE} ==="
echo "API: http://127.0.0.1:7860"
echo "Set Diffusion in Low Bits: Automatic (fp16 LoRA)"

if [[ "$(id -u)" -eq 0 ]]; then
  runuser -u "${FORGE_USER}" -- bash "${DEPLOY}/bootstrap_forge_venv.sh" "${FORGE}"
  run_as_forge_user "${FORGE}" bash -lc "cd '${FORGE}' && ./webui.sh"
else
  bash "${DEPLOY}/bootstrap_forge_venv.sh" "${FORGE}"
  cd "${FORGE}" && ./webui.sh
fi
