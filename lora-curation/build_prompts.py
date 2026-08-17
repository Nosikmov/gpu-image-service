#!/usr/bin/env python3
"""Regenerate lora-curation/prompts.json (100 entries)."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from prompt_pack import write_prompt_pack

if __name__ == "__main__":
    out = _ROOT / "prompts.json"
    pack = write_prompt_pack(out)
    print(f"Wrote {len(pack)} prompts to {out}")
