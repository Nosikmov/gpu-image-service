#!/usr/bin/env python3
"""Rewrite train-a5000/dataset/*.txt from lora-curation/prompts.json (eye-locked captions)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
LORA_CURATION = REPO / "lora-curation"
DATASET = ROOT / "dataset"
PROMPTS_JSON = LORA_CURATION / "prompts.json"

if str(LORA_CURATION) not in sys.path:
    sys.path.insert(0, str(LORA_CURATION))

from caption_train import normalize_training_caption  # noqa: E402
from style import TRIGGER_WORD  # noqa: E402


def main() -> int:
    if not PROMPTS_JSON.is_file():
        print(f"Missing {PROMPTS_JSON}", file=sys.stderr)
        return 1
    if not DATASET.is_dir():
        print(f"Missing {DATASET}", file=sys.stderr)
        return 1

    pack = json.loads(PROMPTS_JSON.read_text(encoding="utf-8"))
    by_id = {str(row["id"]): str(row.get("prompt") or "") for row in pack.get("entries") or []}

    updated = 0
    skipped = 0
    for png in sorted(DATASET.glob("*.png")):
        entry_id = png.stem
        prompt = by_id.get(entry_id, "")
        if not prompt:
            print(f"[skip] {entry_id}: no entry in prompts.json")
            skipped += 1
            continue
        caption = normalize_training_caption(prompt, trigger=TRIGGER_WORD, entry_id=entry_id)
        png.with_suffix(".txt").write_text(caption + "\n", encoding="utf-8")
        print(f"[ok] {entry_id}")
        updated += 1

    print(f"Done: {updated} captions written, {skipped} skipped -> {DATASET}")
    return 0 if updated else 1


if __name__ == "__main__":
    raise SystemExit(main())
