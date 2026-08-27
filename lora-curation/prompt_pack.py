#!/usr/bin/env python3
"""Legacy DreamShaper/medieval prompt pack — unused by default.

Prefer: python build_prompts.py  (reads promts-for-generate.txt via parse_prompts_txt).
Kept for reference / rollback only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Re-export old builder only if explicitly needed
from style import HOUSE_STYLE, STYLE_LOCK  # noqa: E402

STYLE_SUFFIX = (
    f"{STYLE_LOCK}, {HOUSE_STYLE}, "
    "single creature only, plain neutral gray background, no scenery, no text, no sheet"
)


def write_prompt_pack(path: Path) -> list[dict[str, Any]]:
    raise SystemExit(
        "prompt_pack.write_prompt_pack is deprecated. "
        "Use: python build_prompts.py [--variants 2]"
    )


if __name__ == "__main__":
    write_prompt_pack(_ROOT / "prompts.json")
