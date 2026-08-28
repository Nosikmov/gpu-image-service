#!/usr/bin/env bash
# Copy approved curation export into train-a5000/dataset (Linux server).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${SRC:-${ROOT}/../lora-curation/export/approved}"
DST="${DST:-${ROOT}/dataset}"

if [[ ! -d "${SRC}" ]]; then
  echo "Missing ${SRC}" >&2
  echo "Run: python3 lora-curation/export_dataset.py --caption-mode train" >&2
  exit 1
fi

mkdir -p "${DST}"
rsync -av --delete \
  --include='*.png' --include='*.txt' --exclude='*' \
  "${SRC}/" "${DST}/"

PNG_COUNT="$(find "${DST}" -maxdepth 1 -name '*.png' | wc -l | tr -d ' ')"
echo "OK: ${PNG_COUNT} PNG in ${DST}"
