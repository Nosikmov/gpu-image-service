#!/usr/bin/env python3
"""Alias: Forge Flux GGUF batch generator (same as generate_batch_gpu.py)."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from generate_batch_gpu import main

if __name__ == "__main__":
    raise SystemExit(main())
