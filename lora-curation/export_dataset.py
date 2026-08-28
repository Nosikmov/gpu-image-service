#!/usr/bin/env python3
"""Export approved curation images into a LoRA training folder with captions."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import EXPORT_DIR, load_prompts, load_ratings  # noqa: E402
from style import TRIGGER_WORD  # noqa: E402

_LORA_TAG = re.compile(r"<lora:[^>]+>\s*", re.IGNORECASE)
_MULTI_COMMA = re.compile(r"\s*,\s*,+")


def clean_prompt_for_training(prompt: str) -> str:
    """Strip LoRA tags; keep subject/style words for Flux training captions."""
    text = _LORA_TAG.sub("", prompt or "")
    text = _MULTI_COMMA.sub(",", text)
    return text.strip(" ,\n\t")


def make_caption(prompt: str, trigger: str, mode: str) -> str:
    cleaned = clean_prompt_for_training(prompt)
    if mode == "trigger_only":
        return trigger
    if mode == "full":
        # legacy: raw prompt including <lora:...> (not ideal for training)
        return (prompt or "").strip()
    if mode == "trigger":
        return f"{trigger}, {cleaned}" if cleaned else trigger
    # default training mode
    if cleaned.lower().startswith(trigger.lower()):
        return cleaned
    return f"{trigger}, {cleaned}" if cleaned else trigger


def export_approved(*, min_rating: str = "approve", caption_mode: str = "train") -> dict[str, int]:
    ratings = load_ratings()
    pack = load_prompts()
    prompt_by_id = {str(r["id"]): str(r["prompt"]) for r in pack["entries"]}
    trigger = str(pack.get("trigger_word_suggestion") or TRIGGER_WORD)

    allowed = {"approve"} if min_rating == "approve" else {"approve", "maybe"}
    entries = ratings.get("entries") or {}

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    for old in EXPORT_DIR.glob("*"):
        if old.is_file():
            old.unlink()

    copied = 0
    for entry_id, row in entries.items():
        rating = str(row.get("rating") or "")
        if rating not in allowed:
            continue

        src = None
        for ext in ("png", "webp", "jpg", "jpeg"):
            candidate = _ROOT / "images" / f"{entry_id}.{ext}"
            if candidate.is_file():
                src = candidate
                break
        if src is None:
            print(f"[skip] {entry_id}: image missing")
            continue

        dst_img = EXPORT_DIR / src.name
        shutil.copy2(src, dst_img)

        prompt = prompt_by_id.get(entry_id, "")
        caption = make_caption(prompt, trigger, caption_mode)
        dst_img.with_suffix(".txt").write_text(caption + "\n", encoding="utf-8")
        copied += 1
        print(f"[export] {entry_id} -> {dst_img.name}")

    meta = {
        "count": copied,
        "trigger_word": trigger,
        "min_rating": min_rating,
        "caption_mode": caption_mode,
        "export_dir": str(EXPORT_DIR),
    }
    (EXPORT_DIR / "dataset_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(meta, ensure_ascii=False))
    return {"copied": copied}


def main() -> int:
    parser = argparse.ArgumentParser(description="Export approved images for LoRA training")
    parser.add_argument("--include-maybe", action="store_true")
    parser.add_argument(
        "--caption-mode",
        choices=("train", "trigger", "trigger_only", "full"),
        default="train",
        help="train = gf_lowpoly + cleaned prompt (recommended)",
    )
    args = parser.parse_args()
    min_rating = "maybe" if args.include_maybe else "approve"
    export_approved(min_rating=min_rating, caption_mode=args.caption_mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
