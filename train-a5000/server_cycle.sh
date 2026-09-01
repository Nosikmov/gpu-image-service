#!/usr/bin/env bash
# Server-side helpers: train, test LoRA, start round-2 curation.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "${ROOT}/.." && pwd)"
TRAIN_NAME="${TRAIN_NAME:-gf_lowpoly}"
FORGE="${FORGE_DIR:-${FORGE:-/home/sdforge/stable-diffusion-webui-forge}}"
LORA_OUT="${ROOT}/output/${TRAIN_NAME}"

cmd="${1:-help}"

info() { printf '\033[36m==>\033[0m %s\n' "$*"; }

do_train() {
  info "Train ${TRAIN_NAME} (dataset: ${ROOT}/dataset)"
  PNG="$(find "${ROOT}/dataset" -maxdepth 1 -name '*.png' | wc -l | tr -d ' ')"
  if [[ "${PNG}" -lt 10 ]]; then
    echo "Need at least ~10 PNG in dataset/ (have ${PNG}). Upload with push_dataset.bat" >&2
    exit 1
  fi
  cd "${ROOT}"
  TRAIN_NAME="${TRAIN_NAME}" ./bootstrap.sh
}

do_test() {
  local lora="${LORA:-}"
  if [[ -z "${lora}" ]]; then
    lora="$(find "${LORA_OUT}" -maxdepth 1 -name '*.safetensors' 2>/dev/null | sort | tail -1)"
  fi
  if [[ -z "${lora}" || ! -f "${lora}" ]]; then
    echo "No LoRA in ${LORA_OUT}. Run: $0 train" >&2
    exit 1
  fi
  info "Smoke test: ${lora}"
  cd "${ROOT}/test_lora"
  LORA="${lora}" ./run_on_server.sh "${@:2}"
}

do_round2() {
  local src
  src="$(find "${LORA_OUT}" -maxdepth 1 -name '*.safetensors' 2>/dev/null | sort | tail -1)"
  if [[ -z "${src}" || ! -f "${src}" ]]; then
    echo "Train first — no .safetensors in ${LORA_OUT}" >&2
    exit 1
  fi
  mkdir -p "${FORGE}/models/Lora"
  info "Install LoRA for Forge curation: ${src} -> gf_lowpoly.safetensors"
  cp "${src}" "${FORGE}/models/Lora/gf_lowpoly.safetensors"
  info "Stash old curation images (if any)"
  python3 "${REPO}/lora-curation/stash_images.py" --label "before_round2_${TRAIN_NAME}" || true
  export CURATION_MODE=trained
  export FORGE_DIR="${FORGE}"
  info "CURATION_MODE=trained — generate with gf_lowpoly only"
  info "Start Forge in another tmux if needed, then run_curation runs below"
  bash "${REPO}/lora-curation/deploy/run_curation.sh"
}

do_all() {
  do_train
  do_test
  info "Review test_lora/out/ — then: $0 round2 for dataset v2"
}

case "${cmd}" in
  train)   do_train ;;
  test)    do_test "${@:2}" ;;
  round2)  do_round2 ;;
  all)     do_all ;;
  help|*)
    cat <<EOF
Usage: ./server_cycle.sh <command>

  train     — bootstrap.sh (TRAIN_NAME=${TRAIN_NAME})
  test      — diffusers smoke test -> test_lora/out/
  round2    — install LoRA in Forge + curation with CURATION_MODE=trained
  all       — train then test

Env: TRAIN_NAME, HF_TOKEN, HF_REPO_ID, FORGE_DIR, LORA=/path/to.safetensors
EOF
    ;;
esac
