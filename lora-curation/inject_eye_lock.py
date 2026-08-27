# -*- coding: utf-8 -*-
"""Inject EYE_LOCK into training captions (skip special-eye subjects)."""
from __future__ import annotations

import re
from pathlib import Path

EYE_LOCK = (
    "identical paired low-poly cat eyes, two matching oval eyes, flat white sclera, "
    "same size simple black round pupils, symmetrical, no mismatched eyes"
)

# Subjects that intentionally have non-standard eyes — do not overwrite.
SKIP_SUBSTR = (
    "cyclops",
    "button eyes",
    "slit eyes",
    "eye patch",
    "single large",
    "hollow eye",
    "visor over eyes",
    "glowing yellow eyes",  # basilisk etc. — keep fantasy eyes but could still lock shape; skip for now
)

MARKER = "identical paired low-poly cat eyes"


def should_skip(text: str) -> bool:
    low = text.lower()
    return any(s in low for s in SKIP_SUBSTR)


def inject(text: str) -> str:
    text = text.strip()
    if MARKER in text:
        return text
    if should_skip(text):
        return text
    # Insert after "big angular head" if present, else before T-pose / background
    if "big angular head" in text:
        return text.replace("big angular head", f"big angular head, {EYE_LOCK}", 1)
    if ", T-pose" in text:
        return text.replace(", T-pose", f", {EYE_LOCK}, T-pose", 1)
    return f"{text}, {EYE_LOCK}"


def main() -> None:
    roots = [
        Path(__file__).resolve().parents[1] / "train-a5000" / "dataset",
        Path(__file__).resolve().parent / "export" / "approved",
    ]
    changed = 0
    skipped = 0
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.glob("*.txt")):
            old = path.read_text(encoding="utf-8").strip()
            new = inject(old)
            if new != old:
                path.write_text(new + "\n", encoding="utf-8")
                changed += 1
            elif should_skip(old) or MARKER in old:
                skipped += 1
    print(f"updated={changed} already_or_special={skipped}")


if __name__ == "__main__":
    main()
