# -*- coding: utf-8 -*-
"""Remove pose prompts + eye-lock; add four new creature prompts."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent

POSE_IDS = {"three_quarter_view", "idle_action_pose", "sitting_pose", "back_view"}

EYE_LOCK_RE = re.compile(
    r",?\s*identical paired low-poly cat eyes,\s*"
    r"two matching oval eyes,\s*"
    r"flat white sclera,\s*"
    r"same size simple black round pupils,\s*"
    r"symmetrical,\s*"
    r"no mismatched eyes",
    re.IGNORECASE,
)

NEW_ENTRIES = [
    {
        "id": "samurai",
        "title": "Кот-самурай (Samurai Cat)",
        "prompt": (
            "<lora:gf_lowpoly:0.85>, gf_lowpoly, ningraphix, ps1 game screenshot, "
            "anthropomorphic cat samurai, lacquered low-poly armor plates, kabuto helmet with cat ears cutouts, "
            "katana at hip, chibi proportions, big angular head, low-poly mesh, flat shaded, crisp hard edges, "
            "T-pose, neutral solid light grey background"
        ),
    },
    {
        "id": "steampunk_clockwork",
        "title": "Стимпанк-кот (Steampunk Clockwork Cat)",
        "prompt": (
            "<lora:gf_lowpoly:0.85>, gf_lowpoly, ningraphix, ps1 game screenshot, "
            "anthropomorphic clockwork cat, brass low-poly plating, visible gears in chest, "
            "monocle lens, steam vents on shoulders, chibi proportions, big angular head, "
            "low-poly mesh, flat shaded, crisp hard edges, T-pose, neutral solid light grey background"
        ),
    },
    {
        "id": "chef_cook",
        "title": "Кот-повар (Chef Cat)",
        "prompt": (
            "<lora:gf_lowpoly:0.85>, gf_lowpoly, ningraphix, ps1 game screenshot, "
            "anthropomorphic cat chef, tall blocky chef hat, apron, holding a low-poly frying pan, "
            "chibi proportions, big angular head, low-poly mesh, flat shaded, crisp hard edges, "
            "T-pose, neutral solid light grey background"
        ),
    },
    {
        "id": "frost_witch",
        "title": "Морозная ведьма-кот (Frost Witch Cat)",
        "prompt": (
            "<lora:gf_lowpoly:0.85>, gf_lowpoly, ningraphix, ps1 game screenshot, "
            "anthropomorphic cat frost witch, icy blue cloak, crystal staff with frozen tip, "
            "snowflake low-poly ornaments, chibi proportions, big angular head, "
            "low-poly mesh, flat shaded, crisp hard edges, T-pose, neutral solid light grey background"
        ),
    },
]


def strip_eye_lock(text: str) -> str:
    t = EYE_LOCK_RE.sub("", text)
    t = re.sub(r"\s*,\s*,+", ", ", t)
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip(" ,")


def strip_file(path: Path) -> int:
    if not path.is_file():
        return 0
    old = path.read_text(encoding="utf-8").strip()
    new = strip_eye_lock(old)
    if new != old:
        path.write_text(new + "\n", encoding="utf-8")
        return 1
    return 0


def main() -> None:
    # --- prompts.json ---
    pj = ROOT / "prompts.json"
    pack = json.loads(pj.read_text(encoding="utf-8"))
    entries = [e for e in pack.get("entries") or [] if str(e.get("id")) not in POSE_IDS]
    # strip eyes on remaining
    for e in entries:
        e["prompt"] = strip_eye_lock(str(e.get("prompt") or ""))
    existing = {str(e.get("id")) for e in entries}
    for ne in NEW_ENTRIES:
        if ne["id"] not in existing:
            entries.append(
                {
                    "id": ne["id"],
                    "title": ne["title"],
                    "prompt": ne["prompt"],
                    "category": "creature",
                    "monster_id": ne["id"],
                    "variant": "base",
                }
            )
    pack["entries"] = entries
    pack["notes"] = "v2: gf_lowpoly gen; no pose variants; no forced eye lock — curate best eyes by hand"
    pj.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"prompts.json entries={len(entries)}")

    # --- promts-for-generate.txt: rebuild from prompts.json titles+prompts ---
    # Keep file readable: title then prompt
    lines: list[str] = []
    lines.append("# gameFarmling LoRA curation prompts (gf_lowpoly generation)")
    lines.append("# T-pose fullbody only — no pose variants. Eyes not forced; pick best in reviewer.")
    lines.append("")
    for e in entries:
        lines.append(f"{e.get('title') or e['id']}:")
        lines.append(str(e["prompt"]))
        lines.append("")
    (ROOT / "promts-for-generate.txt").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print("promts-for-generate.txt rebuilt")

    # --- style.py ---
    style = ROOT / "style.py"
    text = style.read_text(encoding="utf-8")
    text = re.sub(
        r"\n# Lock default face eyes.*?\"\)\n",
        "\n",
        text,
        count=1,
        flags=re.DOTALL,
    )
    text = text.replace("EYE_LOCK = (\n", "# removed EYE_LOCK\nEYE_LOCK_REMOVED = (\n")
    # cleaner: rewrite style.py simply
    style.write_text(
        '''"""gameFarmling low-poly / PS1 cat style for LoRA curation (Forge + Flux)."""

from __future__ import annotations

HOUSE_STYLE = (
    "ningraphix, ps1 game screenshot, low-poly mesh, flat shaded, crisp hard edges, "
    "chibi proportions, big angular head, neutral solid light grey background"
)

STYLE_LOCK = (
    "anthropomorphic cat, low-poly papercraft / PS1 game look, single character, "
    "full body, centered, no scenery, T-pose"
)

# Flux typically works best with empty or very light negatives.
STYLE_NEGATIVE = ""
MONSTER_NEGATIVE = STYLE_NEGATIVE

TRIGGER_WORD = "gf_lowpoly"

# Use trained LoRA to regenerate the curation set (v2), then retrain.
GENERATION_LORA_TAG = "<lora:gf_lowpoly:0.85>"
GENERATION_PROMPT_PREFIX = f"{GENERATION_LORA_TAG}, {TRIGGER_WORD}, ningraphix, ps1 game screenshot"
''',
        encoding="utf-8",
    )
    print("style.py cleaned")

    # --- train-a5000 dataset captions ---
    ds = REPO / "train-a5000" / "dataset"
    removed = 0
    stripped = 0
    if ds.is_dir():
        for pose in POSE_IDS:
            for ext in (".png", ".txt"):
                p = ds / f"{pose}{ext}"
                if p.exists():
                    p.unlink()
                    removed += 1
        for p in ds.glob("*.txt"):
            stripped += strip_file(p)
        # add caption stubs for new ids (no png until generated)
        for ne in NEW_ENTRIES:
            # training caption without <lora:>
            cap = ne["prompt"]
            cap = re.sub(r"<lora:[^>]+>\s*", "", cap)
            cap = re.sub(r"\s*,\s*,+", ", ", cap).strip(" ,")
            if not cap.lower().startswith("gf_lowpoly"):
                cap = f"gf_lowpoly, {cap}"
            # don't add png-less to train dataset — only after export
    print(f"train dataset removed_pose_files={removed} stripped_eye={stripped}")

    exp = ROOT / "export" / "approved"
    if exp.is_dir():
        for pose in POSE_IDS:
            for ext in (".png", ".txt"):
                p = exp / f"{pose}{ext}"
                if p.exists():
                    p.unlink()
        for p in exp.glob("*.txt"):
            strip_file(p)

    # --- ratings: drop pose, clear new for regen ---
    rp = ROOT / "ratings.json"
    if rp.is_file():
        data = json.loads(rp.read_text(encoding="utf-8"))
        ent = data.setdefault("entries", {})
        for pose in POSE_IDS:
            ent.pop(pose, None)
        for ne in NEW_ENTRIES:
            ent[ne["id"]] = {
                "id": ne["id"],
                "rating": "",
                "note": "new creature prompt",
                "rated_at": "",
            }
        # clear all for regen without eye lock
        for eid, row in ent.items():
            if str(row.get("rating") or ""):
                row["rating"] = ""
                row["note"] = "regen: no eye lock, no poses"
        rp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # --- images for pose ids ---
    img = ROOT / "images"
    if img.is_dir():
        for pose in POSE_IDS:
            for p in img.glob(f"{pose}.*"):
                p.unlink()

    # --- test_lora prompts: strip eye lock from style builders already edited? ---
    for rel in (
        "train-a5000/test_lora/test_gf_lowpoly.py",
        "train-a5000/test_lora/infer_diffusers.py",
    ):
        path = REPO / rel
        if not path.is_file():
            continue
        t = path.read_text(encoding="utf-8")
        t2 = t.replace(
            "chibi proportions, big angular head, identical paired low-poly cat eyes, "
            "two matching oval eyes, flat white sclera, same size simple black round pupils, "
            "symmetrical, no mismatched eyes",
            "chibi proportions, big angular head",
        )
        if t2 != t:
            path.write_text(t2, encoding="utf-8")
            print(f"updated {rel}")

    print("Done. Restart curation to regenerate without eye lock / poses.")


if __name__ == "__main__":
    main()
