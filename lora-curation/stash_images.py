#!/usr/bin/env python3
"""Move current curation images + manifest/ratings to archive/ for a fresh generation run."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import (  # noqa: E402
    IMAGES_DIR,
    MANIFEST_PATH,
    RATINGS_PATH,
    save_manifest,
    save_ratings,
)

_IMAGE_EXTS = {".png", ".webp", ".jpg", ".jpeg"}


def _empty_manifest() -> dict:
    return {"version": 1, "entries": {}}


def _empty_ratings() -> dict:
    return {"version": 1, "entries": {}}


def stash_images(*, label: str | None = None, dry_run: bool = False) -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    folder = f"{stamp}_{label}" if label else stamp
    archive_dir = _ROOT / "archive" / folder
    archive_images = archive_dir / "images"

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    images = sorted(
        p for p in IMAGES_DIR.iterdir() if p.is_file() and p.suffix.lower() in _IMAGE_EXTS
    )
    has_manifest = MANIFEST_PATH.is_file()
    has_ratings = RATINGS_PATH.is_file()

    if not images and not has_manifest and not has_ratings:
        print("Nothing to archive (images/, manifest.json, ratings.json are empty).")
        return archive_dir

    print(f"Archive: {archive_dir}")
    print(f"  images: {len(images)}")

    if dry_run:
        return archive_dir

    archive_images.mkdir(parents=True, exist_ok=True)

    for src in images:
        dst = archive_images / src.name
        shutil.move(str(src), str(dst))
        print(f"  moved {src.name}")

    if has_manifest:
        shutil.copy2(MANIFEST_PATH, archive_dir / "manifest.json")
    if has_ratings:
        shutil.copy2(RATINGS_PATH, archive_dir / "ratings.json")

    save_manifest(_empty_manifest())
    save_ratings(_empty_ratings())
    print("Reset manifest.json and ratings.json for fresh generation.")
    print(f"Done. Restore later: copy from {archive_dir / 'images'} back to images/")
    return archive_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive curation images for a fresh batch")
    parser.add_argument("--label", help="Optional suffix for archive folder name")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    stash_images(label=args.label, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
