# -*- coding: utf-8 -*-
"""Add soft 'feline cat eyes' cue (not the old rigid eye-lock)."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CUR = ROOT / "lora-curation"
TAG = "feline cat eyes"


def ensure(text: str) -> str:
    t = text.strip()
    if re.search(r"\bfeline cat eyes\b", t, re.I):
        return t
    if re.search(r"\bcat eyes\b", t, re.I):
        return re.sub(r"\bcat eyes\b", TAG, t, count=1, flags=re.I)
    if "big angular head" in t:
        return t.replace("big angular head", f"big angular head, {TAG}", 1)
    if ", T-pose" in t:
        return t.replace(", T-pose", f", {TAG}, T-pose", 1)
    return f"{t}, {TAG}"


def main() -> None:
    pj = CUR / "prompts.json"
    pack = json.loads(pj.read_text(encoding="utf-8"))
    n = 0
    for e in pack["entries"]:
        old = e["prompt"]
        new = ensure(old)
        if new != old:
            e["prompt"] = new
            n += 1
    pack["notes"] = (
        "v2: gf_lowpoly gen; soft 'feline cat eyes' cue; curate best faces by hand"
    )
    pj.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("prompts.json", n)

    lines = [
        "# gameFarmling LoRA curation prompts (gf_lowpoly generation)",
        "# T-pose fullbody. Soft cue: feline cat eyes — pick best in reviewer.",
        "",
    ]
    for e in pack["entries"]:
        lines.append(f"{e.get('title') or e['id']}:")
        lines.append(e["prompt"])
        lines.append("")
    (CUR / "promts-for-generate.txt").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )

    for folder in (ROOT / "train-a5000" / "dataset", CUR / "export" / "approved"):
        if not folder.is_dir():
            continue
        c = 0
        for p in folder.glob("*.txt"):
            old = p.read_text(encoding="utf-8").strip()
            old2 = re.sub(
                r",?\s*identical paired low-poly cat eyes[^,]*(?:,[^,]*){0,5}",
                "",
                old,
                flags=re.I,
            )
            new = ensure(old2)
            new = re.sub(r"\s*,\s*,+", ", ", new).strip(" ,")
            if new != old:
                p.write_text(new + "\n", encoding="utf-8")
                c += 1
        print(folder, "updated", c)

    style_path = CUR / "style.py"
    style = style_path.read_text(encoding="utf-8")
    if "feline cat eyes" not in style:
        style = style.replace(
            "chibi proportions, big angular head, neutral solid light grey background",
            "chibi proportions, big angular head, feline cat eyes, neutral solid light grey background",
            1,
        )
        style_path.write_text(style, encoding="utf-8")
        print("style.py ok")

    for rel in (
        "train-a5000/test_lora/test_gf_lowpoly.py",
        "train-a5000/test_lora/infer_diffusers.py",
    ):
        path = ROOT / rel
        t = path.read_text(encoding="utf-8")
        if "feline cat eyes" in t:
            continue
        t2 = t.replace(
            "chibi proportions, big angular head",
            "chibi proportions, big angular head, feline cat eyes",
        )
        path.write_text(t2, encoding="utf-8")
        print("updated", rel)

    print("sample:", pack["entries"][0]["prompt"][100:260])


if __name__ == "__main__":
    main()
