#!/usr/bin/env bash
# webui-user.sh for Forge on Linux GPU server — Flux fp8 + API for curation.
export PYTHON=
export GIT=
# 4090 24GB: full Flux fp8, no --medvram-sdxl
export COMMANDLINE_ARGS="--api --listen --port 7860 --enable-insecure-extension-access"
