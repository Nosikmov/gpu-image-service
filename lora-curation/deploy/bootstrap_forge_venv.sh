#!/usr/bin/env bash
# Fix Forge venv on Ubuntu 24.04+ (CLIP pkg_resources / build isolation).
set -euo pipefail
FORGE="${1:-${FORGE_DIR:-${HOME}/stable-diffusion-webui-forge}}"
CLIP_REF="d50d76daa670286dd6cacf3bcd80b5e4823fc8e1"

if [[ ! -d "${FORGE}" ]]; then
  echo "Forge not found: ${FORGE}" >&2
  exit 1
fi

pick_python() {
  if command -v python3.10 >/dev/null 2>&1; then
    echo python3.10
  elif command -v python3.11 >/dev/null 2>&1; then
    echo python3.11
  else
    echo python3
  fi
}

PY_BIN="$(pick_python)"
echo "==> Python for Forge venv: ${PY_BIN}"

if [[ -d "${FORGE}/venv" ]]; then
  echo "==> Remove broken venv"
  rm -rf "${FORGE}/venv"
fi

"${PY_BIN}" -m venv "${FORGE}/venv"
PY="${FORGE}/venv/bin/python"

"${PY}" -m pip install -U pip wheel
# setuptools 69.x still ships pkg_resources; avoids CLIP isolated-build failure on 3.12
"${PY}" -m pip install "setuptools==69.5.1"

echo "==> Pre-install CLIP (no build isolation)..."
"${PY}" -m pip install --no-build-isolation \
  "git+https://github.com/openai/CLIP.git@${CLIP_REF}"

echo "==> Forge venv ready: ${PY} ($("${PY}" --version))"
