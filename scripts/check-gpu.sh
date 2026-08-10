#!/usr/bin/env bash
set -euo pipefail
# Smoke-check NVIDIA visibility inside a CUDA container (optional).
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
