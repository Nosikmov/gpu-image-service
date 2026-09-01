#!/usr/bin/env bash
# Test trained gf_lowpoly on all 40 prompts from lora-curation/prompts.json
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRAIN="$(cd "${ROOT}/.." && pwd)"
VENV_PY="${TRAIN}/.ai-toolkit/.venv/bin/python"
LORA="${LORA:-${TRAIN}/output/gf_lowpoly/gf_lowpoly.safetensors}"
PROMPTS="${PROMPTS:-${TRAIN}/../lora-curation/prompts.json}"
OUT="${OUT:-${ROOT}/out_dataset}"

export HF_HOME="${HF_HOME:-${TRAIN}/.hf-cache}"
export HF_HUB_CACHE="${HF_HUB_CACHE:-${HF_HOME}/hub}"
export HF_HUB_DISABLE_XET="${HF_HUB_DISABLE_XET:-1}"
export HF_HUB_ENABLE_HF_TRANSFER="${HF_HUB_ENABLE_HF_TRANSFER:-0}"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

if [[ ! -x "${VENV_PY}" ]]; then
  echo "Missing venv: ${VENV_PY} — run bootstrap.sh first"
  exit 1
fi
if [[ ! -f "${LORA}" ]]; then
  echo "Missing LoRA: ${LORA}"
  echo "Hint: LORA=../output/gf_lowpoly/gf_lowpoly_000001500.safetensors $0"
  exit 1
fi

cd "${ROOT}"
echo "==> LoRA:    ${LORA}"
echo "==> Prompts: ${PROMPTS}"
echo "==> Out:     ${OUT}"
"${VENV_PY}" infer_dataset_prompts.py --lora "${LORA}" --prompts "${PROMPTS}" --out "${OUT}" "$@"
ls -lh "${OUT}"/*.png 2>/dev/null | head -20 || true
echo "==> Total: $(find "${OUT}" -maxdepth 1 -name '*.png' | wc -l) images"
