#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> GPU Image Service install"
echo "    root: $ROOT"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "WARNING: this installer targets Ubuntu/Linux GPU hosts."
fi

if [[ -f /etc/os-release ]]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  echo "OS: ${PRETTY_NAME:-unknown}"
  if [[ "${ID:-}" != "ubuntu" && "${ID_LIKE:-}" != *"ubuntu"* && "${ID:-}" != "debian" ]]; then
    echo "WARNING: non-Ubuntu OS detected; continue at your own risk."
  fi
fi

echo "-- Checking NVIDIA driver --"
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi || true
else
  echo "ERROR: nvidia-smi not found. Install NVIDIA proprietary drivers first."
  echo "  Ubuntu: sudo ubuntu-drivers autoinstall && reboot"
  exit 1
fi

echo "-- Checking Docker --"
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker not found. Attempting install via get.docker.com (requires sudo)..."
  if command -v sudo >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker "${SUDO_USER:-$USER}" || true
  else
    echo "ERROR: cannot install Docker without sudo."
    exit 1
  fi
fi
docker --version

if ! docker compose version >/dev/null 2>&1; then
  echo "ERROR: docker compose plugin missing."
  exit 1
fi
docker compose version

echo "-- Checking NVIDIA Container Toolkit --"
if ! docker info 2>/dev/null | grep -qi nvidia; then
  echo "NVIDIA runtime not detected in docker info."
  if [[ "${INSTALL_NVIDIA_TOOLKIT:-0}" == "1" ]] && command -v sudo >/dev/null 2>&1 && [[ -f /etc/os-release ]]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -s -L "https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list" \
      | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
      | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    sudo apt-get update
    sudo apt-get install -y nvidia-container-toolkit
    sudo nvidia-ctk runtime configure --runtime=docker
    sudo systemctl restart docker
  else
    echo "Install NVIDIA Container Toolkit, then re-run:"
    echo "  https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html"
    echo "Or: INSTALL_NVIDIA_TOOLKIT=1 ./scripts/install.sh"
  fi
fi

echo "-- Creating directories --"
MODELS_ROOT="${MODELS_PATH:-$ROOT/data/models}"
GEN_ROOT="${GENERATED_PATH:-$ROOT/data/generated}"
# Prefer paths from existing .env after copy
if [[ ! -f "$ROOT/.env" ]]; then
  cp "$ROOT/.env.example" "$ROOT/.env"
  echo "Created .env from .env.example — set API_KEY before production use."
else
  echo ".env already exists"
fi

# shellcheck disable=SC1091
set -a
source "$ROOT/.env"
set +a

MODELS_ROOT="${MODELS_PATH:-$ROOT/data/models}"
GEN_ROOT="${GENERATED_PATH:-$ROOT/data/generated}"
# Resolve relative paths against repo root
[[ "$MODELS_ROOT" = /* ]] || MODELS_ROOT="$ROOT/${MODELS_ROOT#./}"
[[ "$GEN_ROOT" = /* ]] || GEN_ROOT="$ROOT/${GEN_ROOT#./}"

mkdir -p \
  "$MODELS_ROOT/checkpoints" \
  "$MODELS_ROOT/loras" \
  "$MODELS_ROOT/vae" \
  "$MODELS_ROOT/controlnet" \
  "$GEN_ROOT"

if [[ -z "${API_KEY:-}" || "${API_KEY}" == "change-me-to-a-long-random-string" ]]; then
  echo "WARNING: set a strong API_KEY in .env"
fi

DEFAULT_MODEL_FILE="$MODELS_ROOT/checkpoints/${DEFAULT_MODEL:-sd_xl_base_1.0.safetensors}"
if [[ ! -f "$DEFAULT_MODEL_FILE" ]]; then
  echo "WARNING: checkpoint not found: $DEFAULT_MODEL_FILE"
  echo "Place your model under models/checkpoints/ (see README) or run scripts/fetch-model.sh"
fi

echo "-- Validating docker compose --"
docker compose config >/dev/null
echo "compose config OK"

echo "Install checks finished. Next: ./scripts/start.sh"
