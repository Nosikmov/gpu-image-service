#!/usr/bin/env python3
"""Copy approved curation PNGs into frontend/public/assets/monsters/."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import IMAGES_DIR, load_ratings, monsters_dir  # noqa: E402

try:
    from remove_background import strip_backgrounds  # noqa: E402
except ImportError:
    strip_backgrounds = None  # type: ignore[misc, assignment]

CAT_PREFIX = re.compile(r"^cat_(.+)$")


def curation_id_to_monster_id(entry_id: str) -> str:
    m = CAT_PREFIX.match(entry_id)
    if m:
        return m.group(1)
    return entry_id


def promote(*, only_approved: bool, ids: list[str] | None, remove_bg: bool) -> list[tuple[str, Path]]:
    ratings = load_ratings()
    approved = set()
    if only_approved:
        for eid, row in (ratings.get("entries") or {}).items():
            if row.get("rating") == "approve":
                approved.add(eid)

    dest = monsters_dir()
    dest.mkdir(parents=True, exist_ok=True)
    copied: list[tuple[str, Path]] = []

    for src in sorted(IMAGES_DIR.glob("*.png")):
        entry_id = src.stem
        if ids and entry_id not in ids:
            continue
        if only_approved and entry_id not in approved:
            continue
        monster_id = curation_id_to_monster_id(entry_id)
        dst = dest / f"{monster_id}.png"
        shutil.copy2(src, dst)
        copied.append((monster_id, dst))
        print(f"[promote] {src.name} -> monsters/{monster_id}.png")

    if not copied:
        print("Nothing copied (check images/ and optional --approved-only ratings)")
    else:
        print(f"Done: {len(copied)} monster(s)")
        if remove_bg:
            if strip_backgrounds is None:
                raise SystemExit("remove_background module unavailable")
            strip_backgrounds(
                target="monsters",
                only_approved=only_approved,
                ids=ids,
                dry_run=False,
            )
    return copied


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote curation images to game assets")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Copy all PNGs in images/ (ignore ratings)",
    )
    parser.add_argument(
        "--approved-only",
        action="store_true",
        help="Only entries rated approve in ratings.json",
    )
    parser.add_argument("--ids", nargs="*", help="Specific curation ids (e.g. cat_mob_main_1)")
    parser.add_argument(
        "--remove-bg",
        action="store_true",
        help="OPTIONAL rembg after copy. Do NOT use on already-approved art unless reviewing — rembg can eat creature edges.",
    )
    args = parser.parse_args()
    only_approved = args.approved_only and not args.all
    promote(only_approved=only_approved, ids=args.ids or None, remove_bg=args.remove_bg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
