#!/usr/bin/env bash
# Run 12-image gf_lowpoly smoke test on the GPU server (uses training venv + HF cache).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRAIN="$(cd "${ROOT}/.." && pwd)"
VENV_PY="${TRAIN}/.ai-toolkit/.venv/bin/python"
LORA="${LORA:-${TRAIN}/output/gf_lowpoly/gf_lowpoly.safetensors}"

export HF_HOME="${HF_HOME:-${TRAIN}/.hf-cache}"
export HF_HUB_CACHE="${HF_HUB_CACHE:-${HF_HOME}/hub}"
export HF_HUB_DISABLE_XET="${HF_HUB_DISABLE_XET:-1}"
export HF_HUB_ENABLE_HF_TRANSFER="${HF_HUB_ENABLE_HF_TRANSFER:-0}"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

if [[ ! -x "${VENV_PY}" ]]; then
  echo "Missing toolkit venv: ${VENV_PY}"
  echo "Run train-a5000/bootstrap.sh once first (or point VENV_PY=...)."
  exit 1
fi
if [[ ! -f "${LORA}" ]]; then
  echo "Missing LoRA: ${LORA}"
  exit 1
fi

cd "${ROOT}"
chmod +x infer_diffusers.py 2>/dev/null || true
echo "==> LoRA: ${LORA}"
echo "==> Out:  ${ROOT}/out"
"${VENV_PY}" infer_diffusers.py --lora "${LORA}" --out "${ROOT}/out" "$@"
echo "==> Download folder: ${ROOT}/out"
ls -lh "${ROOT}/out"/*.png 2>/dev/null || true
