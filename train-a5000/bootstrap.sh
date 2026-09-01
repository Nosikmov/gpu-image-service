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

# MUST be set before any Python process imports huggingface_hub (XET hangs on many VPS)
export HF_HUB_DISABLE_XET="${HF_HUB_DISABLE_XET:-1}"
export HF_HUB_ENABLE_HF_TRANSFER="${HF_HUB_ENABLE_HF_TRANSFER:-0}"
export HF_XET_HIGH_PERFORMANCE="${HF_XET_HIGH_PERFORMANCE:-0}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${ROOT}/.." && pwd)"
DATASET="${ROOT}/dataset"
CONFIG_OUT="${ROOT}/runtime/gf_lowpoly_a5000.yaml"
TOOLKIT_DIR="${TOOLKIT_DIR:-${ROOT}/.ai-toolkit}"
OUTPUT_DIR="${ROOT}/output"
HF_CACHE="${ROOT}/.hf-cache"
STEPS="${STEPS:-1500}"
BATCH="${BATCH:-1}"
TRAIN_NAME="${TRAIN_NAME:-gf_lowpoly}"
PY_BIN="${PY_BIN:-python3}"

red() { printf '\033[31m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
info() { printf '\033[36m==>\033[0m %s\n' "$*"; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || { red "Missing command: $1"; exit 1; }
}

info "gf_lowpoly trainer (${TRAIN_NAME})"
info "HF_HUB_DISABLE_XET=${HF_HUB_DISABLE_XET} (must be 1 if downloads stuck at 0B)"
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
# Reduce CUDA fragmentation on 24GB cards (4090 / A5000)
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
# (XET flags already exported at top of script)
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

# Ostris run.py defaults XET on; force-disable in that file + drop xet packages
info "Forcing HTTP Hub downloads (disable XET)..."
if [[ -f "${TOOLKIT_DIR}/run.py" ]]; then
  sed -i \
    -e 's/os.environ\["HF_XET_HIGH_PERFORMANCE"\] = os.getenv("HF_XET_HIGH_PERFORMANCE", "1")/os.environ["HF_XET_HIGH_PERFORMANCE"] = os.getenv("HF_XET_HIGH_PERFORMANCE", "0")/' \
    -e 's/os.environ\["HF_HUB_DISABLE_XET"\] = os.getenv("HF_HUB_DISABLE_XET", "0")/os.environ["HF_HUB_DISABLE_XET"] = os.getenv("HF_HUB_DISABLE_XET", "1")/' \
    "${TOOLKIT_DIR}/run.py" || true
fi
"${VENV_PY}" -m pip uninstall -y hf-xet hf_xet hf_transfer 2>/dev/null || true

info "Logging into Hugging Face..."
"${VENV_PY}" - <<'PY'
import os
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
from huggingface_hub import login
login(token=os.environ["HF_TOKEN"], add_to_git_credential=False)
print("HF login ok; HF_HUB_DISABLE_XET=", os.environ.get("HF_HUB_DISABLE_XET"))
PY

# Pre-download FLUX over plain HTTP so training does not hang on XET "Reconstructing 0B"
if [[ "${SKIP_MODEL_DOWNLOAD:-0}" != "1" && "${UPLOAD_ONLY:-0}" != "1" ]]; then
  info "Pre-downloading FLUX.1-dev into ${HF_HUB_CACHE} (long; watch MB progress)..."
  HF_HUB_DISABLE_XET=1 HF_HUB_ENABLE_HF_TRANSFER=0 HF_XET_HIGH_PERFORMANCE=0 \
  "${VENV_PY}" - <<'PY'
import os
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
os.environ["HF_XET_HIGH_PERFORMANCE"] = "0"
from huggingface_hub import snapshot_download
path = snapshot_download(
    repo_id="black-forest-labs/FLUX.1-dev",
    token=os.environ["HF_TOKEN"],
    resume_download=True,
)
print("FLUX ready at", path)
PY
fi

info "Writing config with absolute paths..."
# Paths must be absolute for Ostris on Linux
DATASET_ABS="$(cd "${DATASET}" && pwd)"
OUTPUT_ABS="$(cd "${OUTPUT_DIR}" && pwd)"
cat > "${CONFIG_OUT}" <<EOF
---
job: extension
config:
  name: ${TRAIN_NAME}
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
        # 24GB VRAM (4090/A5000): samples + EMA often OOM during Flux LoRA
        skip_first_sample: true
        disable_sampling: true
        ema_config:
          use_ema: false
      model:
        name_or_path: "black-forest-labs/FLUX.1-dev"
        is_flux: true
        quantize: true
        quantize_te: true
        low_vram: true
      sample:
        sampler: flowmatch
        sample_every: 99999
        width: 512
        height: 512
        prompts:
          - "gf_lowpoly, ps1 game screenshot, a low-poly 3D character asset of an anthropomorphic cat summoner, dark purple mystic cloak, mystical low-poly runes, empty hands, open palms, identical paired amber yellow cat eyes, flat painted oval eyes, vertical slit pupils, same eye style on every character, chunky low-poly, T-pose, orthographic front view, neutral solid light grey background"
        neg: ""
        seed: 42
        walk_seed: true
        guidance_scale: 3.5
        sample_steps: 20
meta:
  name: ${TRAIN_NAME}
  version: "1.2-24gb"
  trigger: gf_lowpoly
  notes: "24GB VRAM safe: low_vram, no EMA, no mid-train samples"
EOF

info "Starting training (resume from last checkpoint if present)..."
cd "${TOOLKIT_DIR}"
TRAIN_STATUS=0
if [[ "${UPLOAD_ONLY:-0}" != "1" ]]; then
  set +e
  "${VENV_PY}" run.py "${CONFIG_OUT}"
  TRAIN_STATUS=$?
  set -e
else
  info "UPLOAD_ONLY=1 — skip training, upload existing checkpoints"
fi

if [[ "${TRAIN_STATUS}" -ne 0 ]]; then
  red "Training exited with code ${TRAIN_STATUS}"
fi

if [[ "${TRAIN_STATUS}" -eq 0 ]]; then
  green "Done training stage."
  green "LoRA checkpoints: ${OUTPUT_ABS}/${TRAIN_NAME}/"
  ls -lah "${OUTPUT_ABS}/${TRAIN_NAME}/"/*.safetensors 2>/dev/null || true
fi

# --- Deliver weights off the server (so you can leave / kill the box) ---
# Set HF_REPO_ID=YourName/gf-lowpoly  (private by default)
upload_to_hf() {
  local out_dir="${OUTPUT_ABS}/${TRAIN_NAME}"
  if [[ -z "${HF_REPO_ID:-}" ]]; then
    info "No HF_REPO_ID set — skipping Hub upload."
    info "Re-run with: HF_REPO_ID=YourName/gf-lowpoly SKIP_INSTALL=1 UPLOAD_ONLY=1 ./bootstrap.sh"
    return 0
  fi
  if [[ ! -d "${out_dir}" ]]; then
    red "No output dir: ${out_dir}"
    return 1
  fi
  local private="${HF_PRIVATE:-true}"
  info "Uploading LoRA to Hugging Face: ${HF_REPO_ID} (private=${private})"
  HF_PRIVATE_FLAG="${private}" OUT_DIR="${out_dir}" REPO_ID="${HF_REPO_ID}" "${VENV_PY}" - <<'PY'
import os
from pathlib import Path
from huggingface_hub import HfApi, login

token = os.environ["HF_TOKEN"]
login(token=token, add_to_git_credential=False)
api = HfApi(token=token)
repo_id = os.environ["REPO_ID"]
private = os.environ.get("HF_PRIVATE_FLAG", "true").lower() in ("1", "true", "yes")
out = Path(os.environ["OUT_DIR"])
api.create_repo(repo_id=repo_id, repo_type="model", private=private, exist_ok=True)

files = sorted(out.glob("*.safetensors"))
if not files:
    raise SystemExit(f"No .safetensors in {out}")
for f in files:
    print(f"upload {f.name} ...")
    api.upload_file(
        path_or_fileobj=str(f),
        path_in_repo=f.name,
        repo_id=repo_id,
        repo_type="model",
    )
for img in sorted(out.glob("*.png"))[:30]:
    print(f"upload {img.name} ...")
    api.upload_file(
        path_or_fileobj=str(img),
        path_in_repo=f"samples/{img.name}",
        repo_id=repo_id,
        repo_type="model",
    )
url = f"https://huggingface.co/{repo_id}"
print("UPLOADED_OK", url)
Path(os.environ["OUT_DIR"]).joinpath("UPLOADED_TO_HF.txt").write_text(url + "\n", encoding="utf-8")
PY
  green "Download later from: https://huggingface.co/${HF_REPO_ID}"
  green "Then put .safetensors into Forge models/Lora/ — you can power off the server."
}

if [[ "${TRAIN_STATUS}" -eq 0 ]]; then
  upload_to_hf
fi

# --- Phone push via ntfy.sh (no Telegram / Discord) ---
# 1) Install app: https://ntfy.sh (Android/iOS) or open https://ntfy.sh/YOUR_TOPIC in browser
# 2) Subscribe to a long secret topic name
# 3) export NTFY_TOPIC='gf-ready-pickALongSecretWord123'
notify_ntfy() {
  local status="${1:-ok}"
  if [[ -z "${NTFY_TOPIC:-}" ]]; then
    info "No NTFY_TOPIC — skip phone notify. Set it next time to get a push when done."
    return 0
  fi
  need_cmd curl
  local title body ntfy_base tags
  ntfy_base="${NTFY_URL:-https://ntfy.sh}"
  if [[ "${status}" == "ok" ]]; then
    title="gf_lowpoly DONE"
    tags="white_check_mark"
    body="LoRA ready: ${OUTPUT_ABS}/${TRAIN_NAME}/"
    if [[ -n "${HF_REPO_ID:-}" ]]; then
      body="${body}"$'\n'"https://huggingface.co/${HF_REPO_ID}"
    fi
  else
    title="gf_lowpoly FAILED"
    tags="x"
    body="Training failed (exit ${TRAIN_STATUS}). Check tmux on the GPU server."
  fi
  info "ntfy → ${ntfy_base}/${NTFY_TOPIC}"
  curl -fsS \
    -H "Title: ${title}" \
    -H "Priority: high" \
    -H "Tags: ${tags}" \
    -d "${body}" \
    "${ntfy_base}/${NTFY_TOPIC}" >/dev/null \
    && green "Phone notify sent (ntfy)" \
    || red "ntfy send failed — check server outbound HTTPS"
}

if [[ "${TRAIN_STATUS}" -eq 0 ]]; then
  notify_ntfy ok
else
  notify_ntfy fail
  exit "${TRAIN_STATUS}"
fi
