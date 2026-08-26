#!/usr/bin/env bash
# One-shot Flux LoRA train for Ubuntu + NVIDIA (A5000 24GB / 64GB RAM and similar).
# Usage:
#   export HF_TOKEN=hf_xxxxxxxx
#   ./bootstrap.sh
#
# Optional:
#   STEPS=2000 BATCH=1 ./bootstrap.sh
#   SKIP_INSTALL=1 ./bootstrap.sh   # only run train (toolkit already set up)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${ROOT}/.." && pwd)"
DATASET="${ROOT}/dataset"
CONFIG_OUT="${ROOT}/runtime/gf_lowpoly_a5000.yaml"
TOOLKIT_DIR="${TOOLKIT_DIR:-${ROOT}/.ai-toolkit}"
OUTPUT_DIR="${ROOT}/output"
HF_CACHE="${ROOT}/.hf-cache"
STEPS="${STEPS:-1500}"
BATCH="${BATCH:-1}"
PY_BIN="${PY_BIN:-python3}"

red() { printf '\033[31m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
info() { printf '\033[36m==>\033[0m %s\n' "$*"; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || { red "Missing command: $1"; exit 1; }
}

info "gf_lowpoly A5000 trainer"
info "dataset: ${DATASET}"
info "toolkit: ${TOOLKIT_DIR}"

need_cmd git
need_cmd nvidia-smi
need_cmd "${PY_BIN}"

# OpenCV (cv2) needs libGL on headless Ubuntu — otherwise: ImportError: libGL.so.1
if ! ldconfig -p 2>/dev/null | grep -q 'libGL.so.1'; then
  info "Installing libGL for OpenCV (sudo)..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -qq
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
      libgl1 libglib2.0-0 libsm6 libxext6 libxrender1
  else
    red "libGL.so.1 missing. Install OpenGL libs for your distro, then re-run."
    exit 1
  fi
fi

if [[ ! -d "${DATASET}" ]] || [[ -z "$(find "${DATASET}" -maxdepth 1 -name '*.png' | head -1)" ]]; then
  red "No PNG dataset in ${DATASET}"
  red "On Windows run: train-a5000\\sync_dataset.bat"
  exit 1
fi

PNG_COUNT="$(find "${DATASET}" -maxdepth 1 -name '*.png' | wc -l)"
info "images: ${PNG_COUNT}"

if [[ -z "${HF_TOKEN:-}" ]]; then
  red "Set HF_TOKEN (Hugging Face write/read token with access to black-forest-labs/FLUX.1-dev)"
  red "  export HF_TOKEN=hf_..."
  red "Accept the model license: https://huggingface.co/black-forest-labs/FLUX.1-dev"
  exit 1
fi

export HF_TOKEN
export HUGGING_FACE_HUB_TOKEN="${HF_TOKEN}"
export HF_HOME="${HF_CACHE}"
export HF_HUB_CACHE="${HF_CACHE}/hub"
export TRANSFORMERS_CACHE="${HF_CACHE}/transformers"
export TORCH_HOME="${ROOT}/.torch-cache"
mkdir -p "${HF_HUB_CACHE}" "${TRANSFORMERS_CACHE}" "${TORCH_HOME}" "${OUTPUT_DIR}" "${ROOT}/runtime"

nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true

if [[ "${SKIP_INSTALL:-0}" != "1" ]]; then
  if [[ ! -f "${TOOLKIT_DIR}/run.py" ]]; then
    info "Cloning ostris/ai-toolkit..."
    git clone --depth 1 https://github.com/ostris/ai-toolkit.git "${TOOLKIT_DIR}"
  else
    info "ai-toolkit already present"
  fi

  info "Installing / syncing toolkit env (manager)..."
  cd "${TOOLKIT_DIR}"
  # Prefer system python3 for manager bootstrap
  "${PY_BIN}" -m manager sync --force
  cd "${ROOT}"
fi

VENV_PY="${TOOLKIT_DIR}/.venv/bin/python"
if [[ ! -x "${VENV_PY}" ]]; then
  red "Toolkit venv missing: ${VENV_PY}"
  red "Re-run without SKIP_INSTALL=1"
  exit 1
fi

info "Logging into Hugging Face..."
"${VENV_PY}" - <<'PY'
import os
from huggingface_hub import login
login(token=os.environ["HF_TOKEN"], add_to_git_credential=False)
print("HF login ok")
PY

info "Writing config with absolute paths..."
# Paths must be absolute for Ostris on Linux
DATASET_ABS="$(cd "${DATASET}" && pwd)"
OUTPUT_ABS="$(cd "${OUTPUT_DIR}" && pwd)"
cat > "${CONFIG_OUT}" <<EOF
---
job: extension
config:
  name: gf_lowpoly
  process:
    - type: sd_trainer
      training_folder: "${OUTPUT_ABS}"
      device: cuda:0
      trigger_word: "gf_lowpoly"
      network:
        type: lora
        linear: 16
        linear_alpha: 16
      save:
        dtype: float16
        save_every: 250
        max_step_saves_to_keep: 6
      datasets:
        - folder_path: "${DATASET_ABS}"
          caption_ext: txt
          caption_dropout_rate: 0.05
          shuffle_tokens: false
          cache_latents_to_disk: true
          cache_text_embeddings: true
          resolution: [512]
      train:
        batch_size: ${BATCH}
        steps: ${STEPS}
        gradient_accumulation_steps: 1
        train_unet: true
        train_text_encoder: false
        gradient_checkpointing: true
        attention_backend: flash
        xformers: false
        noise_scheduler: flowmatch
        optimizer: adamw8bit
        lr: 0.0001
        dtype: bf16
        cache_text_embeddings: true
        unload_text_encoder: true
        skip_first_sample: false
        disable_sampling: false
        ema_config:
          use_ema: true
          ema_decay: 0.99
      model:
        name_or_path: "black-forest-labs/FLUX.1-dev"
        is_flux: true
        quantize: true
        quantize_te: true
        low_vram: false
      sample:
        sampler: flowmatch
        sample_every: 250
        width: 512
        height: 512
        prompts:
          - "gf_lowpoly, ningraphix, ps1 game screenshot, anthropomorphic cat mage, blue wizard hat, low-poly mesh, flat shaded, crisp hard edges, T-pose, neutral solid light grey background"
          - "gf_lowpoly, ningraphix, ps1 game screenshot, anthropomorphic cat hybrid, orc cat, green fur, tusks, spiked armor, low-poly mesh, flat shaded, T-pose, neutral solid light grey background"
          - "gf_lowpoly, ningraphix, ps1 game screenshot, phoenix cat, fiery low-poly wings, cat head with ears, no scenery, neutral solid light grey background"
        neg: ""
        seed: 42
        walk_seed: true
        guidance_scale: 3.5
        sample_steps: 20
meta:
  name: gf_lowpoly
  version: "1.0-a5000"
  trigger: gf_lowpoly
  notes: "A5000 24GB VRAM + 64GB RAM; curated style dataset"
EOF

info "Starting training (resume from last checkpoint if present)..."
cd "${TOOLKIT_DIR}"
"${VENV_PY}" run.py "${CONFIG_OUT}"

green "Done."
green "LoRA checkpoints: ${OUTPUT_ABS}/gf_lowpoly/"
green "Copy the best *.safetensors to Forge models/Lora/ on your home PC."
ls -lah "${OUTPUT_ABS}/gf_lowpoly/"/*.safetensors 2>/dev/null || true
