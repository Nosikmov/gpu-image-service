#!/usr/bin/env bash
# Sync Forge Flux fp8 models + LoRA to a remote GPU server via rsync.
set -euo pipefail

FORGE_SRC="${FORGE_SRC:-}"
REMOTE="${REMOTE:-}"
export FORGE_DST="${FORGE_DST:-/home/sdforge/stable-diffusion-webui-forge}"

if [[ -z "$FORGE_SRC" || -z "$REMOTE" ]]; then
  cat <<'EOF'
Usage (from Windows Git Bash / WSL / Linux):

  FORGE_SRC=/path/to/stable-diffusion-webui-forge \
  REMOTE=user@gpu-host \
  FORGE_DST=/home/sdforge/stable-diffusion-webui-forge \
  bash lora-curation/deploy/sync_models.sh

Copies Flux fp8 checkpoint, VAE, text encoders, optional gf_lowpoly LoRA.

Optional: RSYNC_OPTS='-avP --progress'
EOF
  exit 1
fi

RSYNC_OPTS="${RSYNC_OPTS:--avP --progress}"

FILES=(
  "models/Stable-diffusion/flux1-dev-fp8.safetensors"
  "models/VAE/ae.safetensors"
  "models/text_encoder/clip_l.safetensors"
  "models/text_encoder/t5xxl_fp8_e4m3fn.safetensors"
)

OPTIONAL=(
  "models/Lora/gf_lowpoly.safetensors"
)

echo "Source: $FORGE_SRC"
echo "Remote: $REMOTE:$FORGE_DST"

for rel in "${FILES[@]}"; do
  src="$FORGE_SRC/$rel"
  if [[ ! -f "$src" ]]; then
    echo "MISSING required: $src" >&2
    exit 1
  fi
done

ssh "$REMOTE" "mkdir -p \
  '$FORGE_DST/models/Stable-diffusion' \
  '$FORGE_DST/models/Lora' \
  '$FORGE_DST/models/VAE' \
  '$FORGE_DST/models/text_encoder'"

for rel in "${FILES[@]}"; do
  echo "=== $rel ==="
  rsync $RSYNC_OPTS "$FORGE_SRC/$rel" "$REMOTE:$FORGE_DST/$rel"
done

for rel in "${OPTIONAL[@]}"; do
  src="$FORGE_SRC/$rel"
  if [[ -f "$src" ]]; then
    echo "=== $rel (optional) ==="
    rsync $RSYNC_OPTS "$src" "$REMOTE:$FORGE_DST/$rel"
  else
    echo "skip optional: $rel"
  fi
done

echo "Done. On server: bash lora-curation/deploy/start_forge.sh"
