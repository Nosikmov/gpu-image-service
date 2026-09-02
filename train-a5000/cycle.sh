#!/usr/bin/env bash
# gf_lowpoly on 4090: train | test (Forge fp8) | setup-forge | captions | round2
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "${ROOT}/.." && pwd)"
TRAIN_NAME="${TRAIN_NAME:-gf_lowpoly}"
FORGE="${FORGE_DIR:-${FORGE:-${HOME}/stable-diffusion-webui-forge}}"
LORA_OUT="${ROOT}/output/${TRAIN_NAME}"
LORA_REPO="${REPO}/loras/${TRAIN_NAME}"

cmd="${1:-help}"
info() { printf '\033[36m==>\033[0m %s\n' "$*"; }

resolve_lora() {
  local lora="${LORA:-}"
  if [[ -z "${lora}" ]]; then
    if [[ -f "${LORA_REPO}/${TRAIN_NAME}.safetensors" ]]; then
      lora="${LORA_REPO}/${TRAIN_NAME}.safetensors"
    else
      lora="$(find "${LORA_OUT}" "${LORA_REPO}" -maxdepth 1 -name '*.safetensors' 2>/dev/null | sort | tail -1)"
    fi
  elif [[ ! -f "${lora}" && -f "${ROOT}/${lora}" ]]; then
    lora="${ROOT}/${lora}"
  elif [[ ! -f "${lora}" && -f "${REPO}/${lora}" ]]; then
    lora="${REPO}/${lora}"
  fi
  if [[ -n "${lora}" && -f "${lora}" ]]; then
    lora="$(cd "$(dirname "${lora}")" && pwd)/$(basename "${lora}")"
  fi
  if [[ -z "${lora}" || ! -f "${lora}" ]]; then
    echo "No LoRA in ${LORA_OUT} or ${LORA_REPO}" >&2
    echo "Run: git lfs pull  OR  LORA=loras/${TRAIN_NAME}/file.safetensors" >&2
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

do_install_loras() {
  local src="${REPO}/loras/${TRAIN_NAME}"
  local boot="${REPO}/loras/bootstrap"
  if [[ ! -d "${src}" ]] || [[ -z "$(find "${src}" -maxdepth 1 -name '*.safetensors' 2>/dev/null | head -1)" ]]; then
    echo "No weights in ${src}. Run: git lfs pull" >&2
    exit 1
  fi
  mkdir -p "${FORGE}/models/Lora"
  info "Install trained LoRA -> Forge models/Lora/"
  local pick="${src}/${TRAIN_NAME}.safetensors"
  if [[ ! -f "${pick}" ]]; then
    pick="$(find "${src}" -maxdepth 1 -name '*.safetensors' | sort | tail -1)"
  fi
  cp "${pick}" "${FORGE}/models/Lora/gf_lowpoly.safetensors"
  info "  gf_lowpoly <- $(basename "${pick}")"
  if [[ -d "${boot}" ]]; then
    for f in "${boot}"/*.safetensors; do
      [[ -f "${f}" ]] || continue
      cp "${f}" "${FORGE}/models/Lora/$(basename "${f}")"
      info "  bootstrap <- $(basename "${f}")"
    done
  fi
  info "Done. Start Forge, then: ./cycle.sh test forge"
}

case "${cmd}" in
  train)         do_train ;;
  test)          do_test "${@}" ;;
  captions)      do_captions ;;
  setup-forge)   do_setup_forge ;;
  install-loras) do_install_loras ;;
  round2)        do_round2 ;;
  help|*)
    cat <<EOF
Usage: ./cycle.sh <command>   (TRAIN_NAME=${TRAIN_NAME})

  train              Ostris FLUX LoRA train
  test [forge|forge40|slow]   test LoRA (default: forge fp8)
  install-loras      copy loras/${TRAIN_NAME}/ -> Forge (after git lfs pull)
  setup-forge        one-time Forge install
  captions           rebuild dataset/*.txt
  round2             Forge curation (trained LoRA only)

Examples:
  export TRAIN_NAME=gf_lowpoly_v2
  git lfs pull
  ./cycle.sh install-loras
  ./cycle.sh test forge --limit 4

Env: TRAIN_NAME, HF_TOKEN, FORGE_DIR, LORA
EOF
    ;;
esac
