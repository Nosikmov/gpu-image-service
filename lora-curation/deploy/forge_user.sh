#!/usr/bin/env bash
# Forge refuses to run as root — use a normal Linux user on rented GPU boxes.
set -euo pipefail

FORGE_USER="${FORGE_USER:-sdforge}"

ensure_forge_user() {
  if [[ "$(id -u)" -ne 0 ]]; then
    return 0
  fi
  if ! id "${FORGE_USER}" &>/dev/null; then
    useradd -m -s /bin/bash "${FORGE_USER}"
    echo "Created user: ${FORGE_USER}"
  fi
  for g in video render; do
    if getent group "${g}" >/dev/null 2>&1; then
      usermod -aG "${g}" "${FORGE_USER}" 2>/dev/null || true
    fi
  done
}

forge_home() {
  if [[ "$(id -u)" -eq 0 ]]; then
    echo "/home/${FORGE_USER}"
  else
    echo "${HOME}"
  fi
}

default_forge_dir() {
  echo "$(forge_home)/stable-diffusion-webui-forge"
}

chown_forge_tree() {
  local dir="$1"
  if [[ "$(id -u)" -eq 0 && -d "${dir}" ]]; then
    chown -R "${FORGE_USER}:${FORGE_USER}" "${dir}"
  fi
}

run_as_forge_user() {
  local forge="$1"
  shift
  if [[ "$(id -u)" -eq 0 ]]; then
  ensure_forge_user
    if ! command -v runuser >/dev/null 2>&1; then
      echo "ERROR: runuser not found (install util-linux)" >&2
      exit 1
    fi
    exec runuser -u "${FORGE_USER}" -- env HOME="/home/${FORGE_USER}" FORGE_DIR="${forge}" "$@"
  else
    exec env FORGE_DIR="${forge}" "$@"
  fi
}
