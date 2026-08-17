#!/usr/bin/env python3
"""Remove backgrounds from curation or game monster PNGs (RGBA, in-place)."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import IMAGES_DIR, load_ratings, monsters_dir  # noqa: E402

CAT_PREFIX = re.compile(r"^cat_(.+)$")


def curation_id_to_monster_id(entry_id: str) -> str:
    m = CAT_PREFIX.match(entry_id)
    if m:
        return m.group(1)
    return entry_id


def _approved_ids() -> set[str]:
    ratings = load_ratings()
    return {
        eid
        for eid, row in (ratings.get("entries") or {}).items()
        if row.get("rating") == "approve"
    }


def _collect_paths(
    *,
    target: str,
    only_approved: bool,
    ids: list[str] | None,
) -> list[Path]:
    approved = _approved_ids() if only_approved else set()
    paths: list[Path] = []

    if target == "curation":
        for src in sorted(IMAGES_DIR.glob("*.png")):
            entry_id = src.stem
            if ids and entry_id not in ids:
                continue
            if only_approved and entry_id not in approved:
                continue
            paths.append(src)
        return paths

    for src in sorted(monsters_dir().glob("*.png")):
        monster_id = src.stem
        if ids:
            wanted = {curation_id_to_monster_id(i) for i in ids}
            if monster_id not in wanted and monster_id not in ids:
                continue
        if only_approved:
            cat_ids = {f"cat_{monster_id}"}
            if not cat_ids & approved:
                continue
        paths.append(src)
    return paths


def remove_background(path: Path) -> None:
    from rembg import remove

    raw = path.read_bytes()
    out = remove(raw)
    path.write_bytes(out)


def strip_backgrounds(
    *,
    target: str,
    only_approved: bool,
    ids: list[str] | None,
    dry_run: bool,
) -> int:
    paths = _collect_paths(target=target, only_approved=only_approved, ids=ids)
    if not paths:
        print("Nothing to process")
        return 0

    for path in paths:
        if dry_run:
            print(f"[dry-run] {path}")
            continue
        remove_background(path)
        print(f"[nobg] {path}")

    print(f"Done: {len(paths)} image(s)")
    return len(paths)


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove PNG backgrounds via rembg")
    parser.add_argument(
        "--target",
        choices=("curation", "monsters"),
        default="monsters",
        help="curation=lora-curation/images, monsters=GAME_REPO/frontend/public/assets/monsters",
    )
    parser.add_argument("--approved-only", action="store_true")
    parser.add_argument("--ids", nargs="*", help="Specific curation or monster ids")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    strip_backgrounds(
        target=args.target,
        only_approved=args.approved_only,
        ids=args.ids or None,
        dry_run=args.dry_run,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
