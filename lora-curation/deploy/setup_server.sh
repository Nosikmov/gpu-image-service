#!/usr/bin/env bash
# One-time Ubuntu prep for RTX 4090: deps + Forge clone + webui-user.sh
set -euo pipefail

REPO="${REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
FORGE="${FORGE:-${HOME}/stable-diffusion-webui-forge}"
DEPLOY="${REPO}/lora-curation/deploy"

info() { printf '\033[36m==>\033[0m %s\n' "$*"; }

info "repo:  ${REPO}"
info "forge: ${FORGE}"

if command -v apt-get >/dev/null 2>&1; then
  APT="apt-get"
  if [[ "$(id -u)" -ne 0 ]] && command -v sudo >/dev/null 2>&1; then
    APT="sudo apt-get"
  fi
  info "Installing system packages..."
  ${APT} update -qq
  DEBIAN_FRONTEND=noninteractive ${APT} install -y -qq \
    git tmux curl rsync \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
    python3 python3-venv
else
  info "No apt-get — install git, tmux, curl, rsync, python3 manually"
fi

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "ERROR: nvidia-smi not found. Install NVIDIA driver first." >&2
  exit 1
fi
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

if [[ ! -d "${FORGE}/.git" ]]; then
  info "Cloning Forge into ${FORGE}..."
  git clone https://github.com/lllyasviel/stable-diffusion-webui-forge.git "${FORGE}"
else
  info "Forge already cloned: ${FORGE}"
fi

info "Installing webui-user.sh..."
cp "${DEPLOY}/webui-user.sh" "${FORGE}/webui-user.sh"
chmod +x "${FORGE}/webui-user.sh" "${DEPLOY}"/*.sh

mkdir -p "${FORGE}/models/Stable-diffusion" \
  "${FORGE}/models/Lora" \
  "${FORGE}/models/VAE" \
  "${FORGE}/models/text_encoder" \
  "${REPO}/lora-curation/images"

info "Done."
info "Next: sync Flux models (deploy/sync_models.sh from Windows)"
info "Then:  tmux → bash lora-curation/deploy/start_forge.sh"
