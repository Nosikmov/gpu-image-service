#!/usr/bin/env bash
# Unified LoRA test runner (Forge fp8 default, diffusers fallback).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRAIN="$(cd "${ROOT}/.." && pwd)"
FORGE="${FORGE_DIR:-${HOME}/stable-diffusion-webui-forge}"
FORGE_URL="${FORGE_URL:-http://127.0.0.1:7860}"
TRAIN_NAME="${TRAIN_NAME:-gf_lowpoly}"
PY="${PY:-python3}"
LORA="${LORA:-}"

usage() {
  cat <<EOF
Usage: ./run.sh <mode> [extra args for python script]

Modes:
  forge          12 prompts via Forge fp8 (~5-15s/img)     -> out/
  forge40        40 dataset prompts via Forge             -> out_forge_dataset/
  slow           12 prompts via diffusers (~60s/img)      -> out/
  slow40         40 prompts via diffusers                 -> out_dataset/

Env: TRAIN_NAME, LORA, FORGE_DIR, FORGE_URL, CURATION_MODE
EOF
}

resolve_lora() {
  if [[ -z "${LORA}" ]]; then
    LORA="$(find "${TRAIN}/output/${TRAIN_NAME}" -maxdepth 1 -name '*.safetensors' 2>/dev/null | sort | tail -1)"
  elif [[ ! -f "${LORA}" && -f "${TRAIN}/${LORA}" ]]; then
    LORA="${TRAIN}/${LORA}"
  fi
  if [[ -z "${LORA}" || ! -f "${LORA}" ]]; then
    echo "Missing LoRA under ${TRAIN}/output/${TRAIN_NAME}/" >&2
    exit 1
  fi
  LORA="$(cd "$(dirname "${LORA}")" && pwd)/$(basename "${LORA}")"
}

install_lora_to_forge() {
  mkdir -p "${FORGE}/models/Lora"
  cp "${LORA}" "${FORGE}/models/Lora/gf_lowpoly.safetensors"
  echo "==> LoRA -> ${FORGE}/models/Lora/gf_lowpoly.safetensors"
}

mode="${1:-forge}"
shift || true

case "${mode}" in
  -h|--help|help) usage; exit 0 ;;
esac

resolve_lora
cd "${ROOT}"

case "${mode}" in
  forge|fp8)
    install_lora_to_forge
    export FORGE_URL FORGE_DIR="${FORGE}" CURATION_MODE="${CURATION_MODE:-trained}"
    exec "${PY}" test_gf_lowpoly.py --forge "${FORGE_URL}" "$@"
    ;;
  forge40|fp8-40|forge-dataset)
    install_lora_to_forge
    export FORGE_URL FORGE_DIR="${FORGE}"
    exec "${PY}" test_forge_dataset.py --forge "${FORGE_URL}" "$@"
    ;;
  slow|diffusers)
    export HF_HOME="${HF_HOME:-${TRAIN}/.hf-cache}"
    exec "${PY}" infer_diffusers.py --lora "${LORA}" --out "${ROOT}/out" "$@"
    ;;
  slow40|diffusers40|dataset)
    export HF_HOME="${HF_HOME:-${TRAIN}/.hf-cache}"
    exec "${PY}" infer_dataset_prompts.py --lora "${LORA}" --out "${ROOT}/out_dataset" "$@"
    ;;
  *)
    echo "Unknown mode: ${mode}" >&2
    usage
    exit 1
    ;;
esac
