#!/usr/bin/env bash
# gf_lowpoly on 4090: train | test (Forge fp8) | setup-forge | captions | round2
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "${ROOT}/.." && pwd)"
TRAIN_NAME="${TRAIN_NAME:-gf_lowpoly}"
FORGE="${FORGE_DIR:-${FORGE:-${HOME}/stable-diffusion-webui-forge}}"
LORA_OUT="${ROOT}/output/${TRAIN_NAME}"

cmd="${1:-help}"
info() { printf '\033[36m==>\033[0m %s\n' "$*"; }

resolve_lora() {
  local lora="${LORA:-}"
  if [[ -z "${lora}" ]]; then
    lora="$(find "${LORA_OUT}" -maxdepth 1 -name '*.safetensors' 2>/dev/null | sort | tail -1)"
  elif [[ ! -f "${lora}" && -f "${ROOT}/${lora}" ]]; then
    lora="${ROOT}/${lora}"
  fi
  if [[ -n "${lora}" && -f "${lora}" ]]; then
    lora="$(cd "$(dirname "${lora}")" && pwd)/$(basename "${lora}")"
  fi
  if [[ -z "${lora}" || ! -f "${lora}" ]]; then
    echo "No LoRA in ${LORA_OUT}" >&2
    return 1
  fi
  LORA="${lora}"
}

do_train() {
  info "Train ${TRAIN_NAME}"
  PNG="$(find "${ROOT}/dataset" -maxdepth 1 -name '*.png' | wc -l | tr -d ' ')"
  if [[ "${PNG}" -lt 10 ]]; then
    echo "Need >=10 PNG in dataset/ (have ${PNG}). Run EXPORT.bat on PC or git pull." >&2
    exit 1
  fi
  cd "${ROOT}"
  TRAIN_NAME="${TRAIN_NAME}" ./bootstrap.sh
}

do_test() {
  resolve_lora || exit 1
  local mode="${2:-forge}"
  cd "${ROOT}/test_lora"
  chmod +x run.sh 2>/dev/null || true
  case "${mode}" in
    forge|fp8|forge40|fp8-40|forge-dataset|slow|slow40|diffusers|diffusers40|dataset)
      info "Test (${mode}): ${LORA}"
      LORA="${LORA}" TRAIN_NAME="${TRAIN_NAME}" ./run.sh "${mode}" "${@:3}"
      ;;
    *)
      info "Test (forge): ${LORA}"
      LORA="${LORA}" TRAIN_NAME="${TRAIN_NAME}" ./run.sh forge "${@:2}"
      ;;
  esac
}

do_captions() {
  info "Rebuild dataset/*.txt from prompts.json"
  python3 "${ROOT}/rebuild_captions.py"
}

do_setup_forge() {
  local backup=""
  if [[ -f "${FORGE}/models/Lora/gf_lowpoly.safetensors" ]]; then
    backup="$(mktemp /tmp/gf_lowpoly.XXXXXX.safetensors)"
    cp "${FORGE}/models/Lora/gf_lowpoly.safetensors" "${backup}"
  fi
  if [[ -d "${FORGE}" && ! -f "${FORGE}/webui.sh" ]]; then
    info "Remove incomplete Forge: ${FORGE}"
    rm -rf "${FORGE}"
  fi
  bash "${REPO}/lora-curation/deploy/setup_server.sh"
  if [[ -n "${backup}" && -f "${backup}" ]]; then
    mkdir -p "${FORGE}/models/Lora"
    cp "${backup}" "${FORGE}/models/Lora/gf_lowpoly.safetensors"
    rm -f "${backup}"
  fi
  if resolve_lora 2>/dev/null; then
    mkdir -p "${FORGE}/models/Lora"
    cp "${LORA}" "${FORGE}/models/Lora/gf_lowpoly.safetensors"
    info "Installed LoRA: ${LORA}"
  fi
  cat <<EOF

Next:
  1) Sync models from PC: bash lora-curation/deploy/sync_models.sh
  2) tmux: bash lora-curation/deploy/start_forge.sh
  3) Test: TRAIN_NAME=${TRAIN_NAME} ./cycle.sh test forge

EOF
}

do_round2() {
  resolve_lora || exit 1
  mkdir -p "${FORGE}/models/Lora"
  info "LoRA -> Forge: ${LORA}"
  cp "${LORA}" "${FORGE}/models/Lora/gf_lowpoly.safetensors"
  python3 "${REPO}/lora-curation/stash_images.py" --label "before_round2_${TRAIN_NAME}" 2>/dev/null || true
  export CURATION_MODE=trained FORGE_DIR="${FORGE}"
  bash "${REPO}/lora-curation/deploy/run_curation.sh"
}

case "${cmd}" in
  train)        do_train ;;
  test)         do_test "${@}" ;;
  captions)     do_captions ;;
  setup-forge)  do_setup_forge ;;
  round2)       do_round2 ;;
  help|*)
    cat <<EOF
Usage: ./cycle.sh <command>   (TRAIN_NAME=${TRAIN_NAME})

  train              Ostris FLUX LoRA train (bootstrap.sh)
  test [mode]        Forge fp8 test (default: forge)
                     modes: forge | forge40 | slow | slow40
  captions           rebuild train-a5000/dataset/*.txt
  setup-forge        one-time Forge install on server
  round2             Forge curation with trained LoRA only

Examples:
  export HF_TOKEN=hf_... TRAIN_NAME=gf_lowpoly_v2
  ./cycle.sh train
  ./cycle.sh test forge --limit 4
  ./cycle.sh test forge40

Env: TRAIN_NAME, HF_TOKEN, HF_REPO_ID, FORGE_DIR, LORA
EOF
    ;;
esac
