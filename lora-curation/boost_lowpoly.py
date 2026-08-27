# -*- coding: utf-8 -*-
"""Push prompts toward extreme low-poly / few polygons (less smooth mesh)."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CUR = ROOT / "lora-curation"

# Stronger than the old "low-poly mesh, flat shaded, crisp hard edges"
LOWPOLY_BLOCK = (
    "extremely low-poly, very few polygons, chunky blocky mesh, large flat facets, "
    "minimal geometric detail, PS1 N64 game asset, flat shaded, hard silhouette edges, "
    "no smooth subdivision, no high-poly sculpt"
)

OLD_STYLE_BLOCK = re.compile(
    r"low-poly mesh,\s*flat shaded,\s*crisp hard edges",
    re.IGNORECASE,
)
# Avoid stacking if already boosted
ALREADY = "extremely low-poly"


def boost(text: str) -> str:
    t = text.strip()
    if ALREADY in t.lower():
        # refresh block if an older boost exists — normalize
        t = re.sub(
            r"extremely low-poly,\s*very few polygons,\s*chunky blocky mesh,\s*"
            r"large flat facets,\s*minimal geometric detail,\s*PS1 N64 game asset,\s*"
            r"flat shaded,\s*hard silhouette edges,\s*no smooth subdivision,\s*"
            r"no high-poly sculpt",
            LOWPOLY_BLOCK,
            t,
            flags=re.I,
        )
        return t
    if OLD_STYLE_BLOCK.search(t):
        return OLD_STYLE_BLOCK.sub(LOWPOLY_BLOCK, t, count=1)
    # insert before T-pose / background
    if ", T-pose" in t:
        return t.replace(", T-pose", f", {LOWPOLY_BLOCK}, T-pose", 1)
    return f"{t}, {LOWPOLY_BLOCK}"


def bump_lora_weight(text: str, weight: str = "0.95") -> str:
    return re.sub(
        r"<lora:gf_lowpoly:[0-9.]+>",
        f"<lora:gf_lowpoly:{weight}>",
        text,
        flags=re.I,
    )


def main() -> None:
    pj = CUR / "prompts.json"
    pack = json.loads(pj.read_text(encoding="utf-8"))
    n = 0
    for e in pack["entries"]:
        old = e["prompt"]
        new = boost(bump_lora_weight(old))
        if new != old:
            e["prompt"] = new
            n += 1
    pack["notes"] = (
        "v2: gf_lowpoly@0.95; extreme low-poly / few polygons emphasis; feline cat eyes soft cue"
    )
    pj.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("prompts.json", n)

    lines = [
        "# gameFarmling LoRA curation — extreme low-poly emphasis",
        "# Soft: feline cat eyes. Strong: very few polygons / chunky PS1 mesh.",
        "",
    ]
    for e in pack["entries"]:
        lines.append(f"{e.get('title') or e['id']}:")
        lines.append(e["prompt"])
        lines.append("")
    (CUR / "promts-for-generate.txt").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )

    (CUR / "style.py").write_text(
        f'''"""gameFarmling low-poly / PS1 cat style for LoRA curation (Forge + Flux)."""

from __future__ import annotations

HOUSE_STYLE = (
    "ningraphix, ps1 game screenshot, {LOWPOLY_BLOCK}, "
    "chibi proportions, big angular head, feline cat eyes, neutral solid light grey background"
)

STYLE_LOCK = (
    "anthropomorphic cat, extremely low-poly PS1 game look, single character, "
    "full body, centered, no scenery, T-pose"
)

STYLE_NEGATIVE = ""
MONSTER_NEGATIVE = STYLE_NEGATIVE

TRIGGER_WORD = "gf_lowpoly"

GENERATION_LORA_TAG = "<lora:gf_lowpoly:0.95>"
GENERATION_PROMPT_PREFIX = f"{{GENERATION_LORA_TAG}}, {{TRIGGER_WORD}}, ningraphix, ps1 game screenshot"
''',
        encoding="utf-8",
    )
    print("style.py rewritten")

    for folder in (ROOT / "train-a5000" / "dataset", CUR / "export" / "approved"):
        if not folder.is_dir():
            continue
        c = 0
        for p in folder.glob("*.txt"):
            old = p.read_text(encoding="utf-8").strip()
            new = boost(old)
            # training captions should not keep <lora> tags if any
            new = re.sub(r"<lora:[^>]+>\s*", "", new)
            new = re.sub(r"\s*,\s*,+", ", ", new).strip(" ,")
            if new != old:
                p.write_text(new + "\n", encoding="utf-8")
                c += 1
        print(folder.name, c)

    # test harness style strings
    for rel in (
        "train-a5000/test_lora/test_gf_lowpoly.py",
        "train-a5000/test_lora/infer_diffusers.py",
        "train-a5000/test_lora/test_prompts.json",
    ):
        path = ROOT / rel
        if not path.is_file():
            continue
        t = path.read_text(encoding="utf-8")
        t2 = t.replace("low-poly mesh, flat shaded, crisp hard edges", LOWPOLY_BLOCK)
        t2 = t2.replace('"lora_weight": 0.85', '"lora_weight": 0.95')
        if "extremely low-poly" not in t2 and "chibi proportions, big angular head" in t2:
            t2 = t2.replace(
                "chibi proportions, big angular head, feline cat eyes",
                f"chibi proportions, big angular head, feline cat eyes, {LOWPOLY_BLOCK}",
            )
        if t2 != t:
            path.write_text(t2, encoding="utf-8")
            print("updated", rel)

    print("sample:", pack["entries"][0]["prompt"][90:320])


if __name__ == "__main__":
    main()
