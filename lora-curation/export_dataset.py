#!/usr/bin/env python3
"""Export approved curation images into a LoRA training folder with captions."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import EXPORT_DIR, load_prompts, load_ratings  # noqa: E402


def export_approved(*, min_rating: str = "approve", caption_mode: str = "full") -> dict[str, int]:
    ratings = load_ratings()
    pack = load_prompts()
    prompt_by_id = {str(r["id"]): str(r["prompt"]) for r in pack["entries"]}
    trigger = str(pack.get("trigger_word_suggestion") or "gf_bestiary")

    allowed = {"approve"} if min_rating == "approve" else {"approve", "maybe"}
    entries = ratings.get("entries") or {}

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    # Clean previous export
    for old in EXPORT_DIR.glob("*"):
        if old.is_file():
            old.unlink()

    copied = 0
    for entry_id, row in entries.items():
        rating = str(row.get("rating") or "")
        if rating not in allowed:
            continue
        image_rel = f"images/{entry_id}.png"
        for ext in ("png", "webp", "jpg", "jpeg"):
            candidate = _ROOT / "images" / f"{entry_id}.{ext}"
            if candidate.is_file():
                image_rel = f"images/{entry_id}.{ext}"
                break
        src = _ROOT / image_rel
        if not src.is_file():
            print(f"[skip] {entry_id}: image missing")
            continue

        dst_img = EXPORT_DIR / src.name
        shutil.copy2(src, dst_img)

        prompt = prompt_by_id.get(entry_id, "")
        if caption_mode == "trigger":
            caption = f"{trigger}, {prompt}"
        elif caption_mode == "trigger_only":
            caption = trigger
        else:
            caption = prompt

        dst_txt = dst_img.with_suffix(".txt")
        dst_txt.write_text(caption.strip() + "\n", encoding="utf-8")
        copied += 1
        print(f"[export] {entry_id} -> {dst_img.name}")

    meta = {
        "count": copied,
        "trigger_word": trigger,
        "min_rating": min_rating,
        "caption_mode": caption_mode,
    }
    (EXPORT_DIR / "dataset_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(meta, ensure_ascii=False))
    return {"copied": copied}


def main() -> int:
    parser = argparse.ArgumentParser(description="Export approved images for LoRA training")
    parser.add_argument(
        "--include-maybe",
        action="store_true",
        help="Also export entries rated 'maybe'",
    )
    parser.add_argument(
        "--caption-mode",
        choices=("full", "trigger", "trigger_only"),
        default="full",
        help="Caption file content for each image",
    )
    args = parser.parse_args()
    min_rating = "maybe" if args.include_maybe else "approve"
    export_approved(min_rating=min_rating, caption_mode=args.caption_mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
