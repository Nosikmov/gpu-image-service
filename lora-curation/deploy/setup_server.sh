#!/usr/bin/env bash
# One-time Ubuntu prep for RTX 4090: deps + Forge clone + webui-user.sh
set -euo pipefail

REPO="${REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
DEPLOY="${REPO}/lora-curation/deploy"
# shellcheck source=forge_user.sh
source "${DEPLOY}/forge_user.sh"

FORGE="${FORGE:-$(default_forge_dir)}"

info() { printf '\033[36m==>\033[0m %s\n' "$*"; }

info "repo:  ${REPO}"
info "forge: ${FORGE}"
if [[ "$(id -u)" -eq 0 ]]; then
  info "root detected — Forge will use user: ${FORGE_USER}"
fi

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

if [[ "$(id -u)" -eq 0 ]]; then
  ensure_forge_user
fi

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "ERROR: nvidia-smi not found. Install NVIDIA driver first." >&2
  exit 1
fi
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

# Migrate Forge cloned under /root by mistake
if [[ "$(id -u)" -eq 0 && -d /root/stable-diffusion-webui-forge && ! -d "${FORGE}/.git" ]]; then
  info "Moving /root/stable-diffusion-webui-forge → ${FORGE}"
  mkdir -p "$(dirname "${FORGE}")"
  mv /root/stable-diffusion-webui-forge "${FORGE}"
fi

if [[ ! -d "${FORGE}/.git" ]]; then
  if [[ -d "${FORGE}" && ! -f "${FORGE}/webui.sh" ]]; then
    info "Removing incomplete Forge directory: ${FORGE}"
    rm -rf "${FORGE}"
  fi
  info "Cloning Forge into ${FORGE}..."
  if [[ "$(id -u)" -eq 0 ]]; then
    runuser -u "${FORGE_USER}" -- git clone https://github.com/lllyasviel/stable-diffusion-webui-forge.git "${FORGE}"
  else
    git clone https://github.com/lllyasviel/stable-diffusion-webui-forge.git "${FORGE}"
  fi
else
  info "Forge already cloned: ${FORGE}"
fi

info "Installing webui-user.sh..."
cp "${DEPLOY}/webui-user.sh" "${FORGE}/webui-user.sh"
chmod +x "${FORGE}/webui-user.sh" "${DEPLOY}"/*.sh
chown_forge_tree "${FORGE}"

mkdir -p "${FORGE}/models/Stable-diffusion" \
  "${FORGE}/models/Lora" \
  "${FORGE}/models/VAE" \
  "${FORGE}/models/text_encoder" \
  "${REPO}/lora-curation/images"
chown_forge_tree "${FORGE}/models"

info "Done."
info "Forge path: ${FORGE}"
if [[ "$(id -u)" -eq 0 ]]; then
  info "Sync models to: ${FORGE} (user ${FORGE_USER})"
fi
info "Next: sync Flux models (deploy/sync_models.sh from Windows)"
info "Then:  tmux → bash lora-curation/deploy/start_forge.sh"
