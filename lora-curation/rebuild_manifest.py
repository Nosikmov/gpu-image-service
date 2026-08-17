#!/usr/bin/env python3
"""Rebuild manifest.json from PNG/WebP files in images/."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import IMAGES_DIR, find_image_rel, load_prompts, load_manifest, save_manifest  # noqa: E402


def main() -> int:
    pack = load_prompts()
    manifest = load_manifest()
    manifest.setdefault("version", 1)
    store = manifest.setdefault("entries", {})
    added = 0
    for row in pack["entries"]:
        entry_id = str(row["id"])
        rel = find_image_rel(entry_id)
        if not rel:
            continue
        store[entry_id] = {
            "id": entry_id,
            "prompt": row.get("prompt"),
            "image": rel,
            "status": "ok",
            "rebuilt": True,
        }
        added += 1
    manifest["updated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    save_manifest(manifest)
    print(f"manifest entries with images: {added}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
