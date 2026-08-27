# -*- coding: utf-8 -*-
"""Switch curation generation from dual style LoRAs to trained gf_lowpoly."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OLD = re.compile(
    r"<lora:Low_Poly_Papercraft:[^>]+>\s*<lora:ningraphix:[^>]+>\s*,?\s*",
    re.IGNORECASE,
)
# Also catch single leftover tags
OLD_ANY = re.compile(
    r"<lora:(?:Low_Poly_Papercraft|ningraphix):[^>]+>\s*,?\s*",
    re.IGNORECASE,
)
NEW_PREFIX = "<lora:gf_lowpoly:0.85>, gf_lowpoly, "


def rewrite_prompt(text: str) -> str:
    t = text.strip()
    t = OLD.sub("", t)
    t = OLD_ANY.sub("", t)
    # avoid double gf_lowpoly prefix
    if t.lower().startswith("<lora:gf_lowpoly"):
        return t
    if t.lower().startswith("gf_lowpoly,"):
        return NEW_PREFIX + t[len("gf_lowpoly,") :].lstrip(" ,")
    # drop leading ningraphix duplicate if present after strip
    if t.lower().startswith("ningraphix,"):
        return NEW_PREFIX + t
    return NEW_PREFIX + t


def main() -> None:
    # 1) source txt
    pt = ROOT / "promts-for-generate.txt"
    lines = pt.read_text(encoding="utf-8").splitlines()
    out = []
    n = 0
    for line in lines:
        if "<lora:" in line.lower() or line.strip().startswith("ningraphix,"):
            new = rewrite_prompt(line) if "<lora:" in line.lower() or "ningraphix" in line.lower() else line
            # only rewrite prompt lines
            if line.strip().startswith("<lora:") or (
                "ps1 game screenshot" in line and "ningraphix" in line
            ):
                new = rewrite_prompt(line)
                if new != line:
                    n += 1
                out.append(new)
            else:
                out.append(line)
        else:
            out.append(line)
    pt.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"promts-for-generate.txt lines changed={n}")

    # 2) prompts.json
    pj = ROOT / "prompts.json"
    pack = json.loads(pj.read_text(encoding="utf-8"))
    m = 0
    for e in pack.get("entries") or []:
        old = str(e.get("prompt") or "")
        new = rewrite_prompt(old)
        if new != old:
            e["prompt"] = new
            m += 1
    pack["trigger_word_suggestion"] = "gf_lowpoly"
    pack["generation_lora"] = "gf_lowpoly"
    pack["notes"] = "v2 dataset: generate with trained gf_lowpoly + eye lock, then retrain"
    pj.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"prompts.json entries changed={m}")

    # 3) clear ratings + delete images so auto_loop regenerates
    ratings_path = ROOT / "ratings.json"
    cleared = 0
    if ratings_path.is_file():
        data = json.loads(ratings_path.read_text(encoding="utf-8"))
        for eid, row in (data.get("entries") or {}).items():
            if str(row.get("rating") or ""):
                row["rating"] = ""
                row["note"] = "regen v2 with gf_lowpoly + uniform eyes"
                cleared += 1
        ratings_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"ratings cleared={cleared}")

    img_dir = ROOT / "images"
    removed = 0
    if img_dir.is_dir():
        for p in img_dir.glob("*"):
            if p.suffix.lower() in {".png", ".webp", ".jpg", ".jpeg"}:
                p.unlink()
                removed += 1
    print(f"images removed={removed}")
    print("Next: START_CURATION.bat  (Forge + gf_lowpoly.safetensors in models/Lora)")


if __name__ == "__main__":
    main()
