#!/usr/bin/env python3
"""Archive current prompts files before switching to a new prompt pack."""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
PROMPTS_TXT = _ROOT / "promts-for-generate.txt"
PROMPTS_JSON = _ROOT / "prompts.json"


def stash_prompts(*, label: str | None = None, dry_run: bool = False) -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    folder = f"{stamp}_{label}" if label else stamp
    archive_dir = _ROOT / "archive" / "prompts" / folder

    sources = [p for p in (PROMPTS_TXT, PROMPTS_JSON) if p.is_file()]
    if not sources:
        print("Nothing to archive (no promts-for-generate.txt or prompts.json).")
        return archive_dir

    print(f"Archive prompts -> {archive_dir}")
    for src in sources:
        print(f"  {src.name}")
    if dry_run:
        return archive_dir

    archive_dir.mkdir(parents=True, exist_ok=True)
    for src in sources:
        shutil.copy2(src, archive_dir / src.name)
    print("Done (copies kept in archive; promts-for-generate.txt will be replaced).")
    return archive_dir


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    stash_prompts(label=args.label, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
