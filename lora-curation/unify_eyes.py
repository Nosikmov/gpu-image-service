# -*- coding: utf-8 -*-
"""Force one shared eye style across captions/prompts (dataset consistency)."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent

EYE_LOCK = (
    "identical paired low-poly cat eyes, two matching oval eyes, flat white sclera, "
    "same size simple black round pupils, symmetrical, no mismatched eyes"
)
MARKER = "identical paired low-poly cat eyes"

# Strip creature-specific eye wording so the LoRA learns one face.
EYE_PHRASES = [
    r"glowing yellow eyes",
    r"glowing ember eyes",
    r"glowing blue eyes(?: through wraps)?",
    r"glowing white eyes",
    r"crimson eyes",
    r"red glowing eyes",
    r"reptilian slit eyes",
    r"button eyes",
    r"neon visor over eyes",
    r"glowing hollow eye sockets",
    r"eye patch",
    r"single large glowing eye in center of forehead",
]

SKIP_IDS = {"cyclops"}  # keep one-eye identity


def strip_eye_phrases(text: str) -> str:
    out = text
    for pat in EYE_PHRASES:
        out = re.sub(pat, "", out, flags=re.IGNORECASE)
    out = re.sub(r"\s*,\s*,+", ", ", out)
    out = re.sub(r"\s{2,}", " ", out)
    return out.strip(" ,")


def inject(text: str) -> str:
    text = strip_eye_phrases(text.strip())
    if MARKER in text:
        return text
    if "big angular head" in text:
        return text.replace("big angular head", f"big angular head, {EYE_LOCK}", 1)
    if ", T-pose" in text:
        return text.replace(", T-pose", f", {EYE_LOCK}, T-pose", 1)
    return f"{text}, {EYE_LOCK}"


def process_txt_dir(folder: Path) -> tuple[int, int]:
    changed = skipped = 0
    if not folder.is_dir():
        return 0, 0
    for path in sorted(folder.glob("*.txt")):
        if path.stem in SKIP_IDS:
            skipped += 1
            continue
        old = path.read_text(encoding="utf-8").strip()
        new = inject(old)
        if new != old:
            path.write_text(new + "\n", encoding="utf-8")
            changed += 1
    return changed, skipped


def process_prompts_json(path: Path) -> int:
    if not path.is_file():
        return 0
    pack = json.loads(path.read_text(encoding="utf-8"))
    n = 0
    for e in pack.get("entries") or []:
        eid = str(e.get("id") or e.get("monster_id") or "")
        if eid in SKIP_IDS:
            continue
        old = str(e.get("prompt") or "")
        new = inject(old)
        if new != old:
            e["prompt"] = new
            n += 1
    path.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return n


def process_promts_txt(path: Path) -> int:
    if not path.is_file():
        return 0
    lines = path.read_text(encoding="utf-8").splitlines()
    out = []
    n = 0
    for line in lines:
        if line.startswith("<lora:") and "cyclops" not in line.lower():
            new = inject(line)
            if new != line:
                n += 1
            out.append(new)
        else:
            out.append(line)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return n


def clear_ratings_for_regen(path: Path) -> int:
    """Clear approve so curation regenerates faces with new eye lock."""
    if not path.is_file():
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("entries") or {}
    n = 0
    for eid, row in list(entries.items()):
        if eid in SKIP_IDS:
            continue
        if str(row.get("rating") or "") in {"approve", "maybe", "reject"}:
            row["rating"] = ""
            row["note"] = "regen eyes: uniform eye lock"
            n += 1
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return n


def main() -> None:
    c1, s1 = process_txt_dir(REPO / "train-a5000" / "dataset")
    c2, s2 = process_txt_dir(ROOT / "export" / "approved")
    pj = process_prompts_json(ROOT / "prompts.json")
    pt = process_promts_txt(ROOT / "promts-for-generate.txt")
    # Also update style helper used by tests already has EYE_LOCK
    rr = clear_ratings_for_regen(ROOT / "ratings.json")
    print(f"train-a5000 captions updated={c1} skipped={s1}")
    print(f"export captions updated={c2} skipped={s2}")
    print(f"prompts.json updated={pj}")
    print(f"promts-for-generate.txt updated={pt}")
    print(f"ratings cleared for regen={rr}")
    print("Next: regenerate images (START_CURATION / auto_loop), approve, export, sync_dataset, retrain.")


if __name__ == "__main__":
    main()
