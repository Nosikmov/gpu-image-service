#!/usr/bin/env python3
"""Parse promts-for-generate.txt into structured curation entries."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from style import (  # noqa: E402
    CHARACTER_BODY,
    FELINE_EYE_LOCK,
    GENERATION_PROMPT_PREFIX,
    PROMPT_FRAMING,
    STYLE_LOCK,
    TRIGGER_WORD,
)

_ROOT = Path(__file__).resolve().parent

# Only strip tokens duplicated by GENERATION_PROMPT_PREFIX / framing (not costume words).
_STRIP_PHRASES: tuple[str, ...] = (
    "gf_lowpoly,",
    "ningraphix,",
    "ps1 game screenshot,",
    "T-pose,",
    "neutral solid light grey background",
    "plain solid light grey background",
    "no scenery",
    "no environment",
    "empty background",
    "chunky low-poly, simple geometric forms, large clean flat facets, PS1 game character, flat shaded, crisp silhouette, limited detail",
    "chunky low-poly, simple geometric forms, flat shaded, crisp silhouette",
    "very low polygon mesh, extremely chunky blocky silhouette, few large geometric facets, highly optimized game model, minimal geometry",
    "crisp stylized hand-painted textures, rich clean color blocks, sharp material definition, painted PS1 textures on flat facets",
    "chibi proportions, big angular head",
    "feline cat eyes",
    "angular slanted feline cat eyes, narrow cat pupils, not round eyes",
)

# Held weapons, props, and worn item clutter — stripped for clean character silhouettes.
_WEAPON_ITEM_RES: tuple[re.Pattern[str], ...] = (
    re.compile(r",?\s*holding\s+[^,]+", re.I),
    re.compile(r",?\s*holds\s+[^,]+", re.I),
    re.compile(r",?\s*quiver with arrows on back", re.I),
    re.compile(r",?\s*katana on back", re.I),
    re.compile(r",?\s*katana at hip", re.I),
    re.compile(r",?\s*blocky hook hand", re.I),
    re.compile(r",?\s*giant club weapon", re.I),
    re.compile(r",?\s*holy emblem shield", re.I),
    re.compile(r",?\s*emblem shield", re.I),
    re.compile(r",?\s*oxygen tank on back", re.I),
    re.compile(r",?\s*belt of vials", re.I),
    re.compile(r",?\s*with a [^,]*(staff|orb|bow|sword|axe|dagger|spear|scythe|club|cleaver|pitchfork|lute|pan|goblet|chest|shield|flask|vial)[^,]*", re.I),
)

_WEAPON_ITEM_PHRASES: tuple[str, ...] = (
    "tall wooden staff with a glowing polygonal crystal tip",
    "glowing magical orb floating above palm",
    "simple polygonal wooden bow",
    "polygonal wooden bow",
    "flat polygonal sword",
    "polygonal sword",
    "glowing polygonal sword",
    "flintlock pistol",
    "small polygonal dagger",
    "polygonal dagger",
    "polygonal battle axe",
    "battle axe",
    "low-poly wooden spear",
    "polygonal scythe",
    "jagged polygonal war cleaver",
    "war cleaver",
    "small low-poly pot of gold",
    "pot of gold",
    "blocky bone club",
    "bone club",
    "polygonal labrys axe",
    "labrys axe",
    "polygonal pitchfork",
    "bubbling low-poly potion flasks",
    "low-poly lute",
    "low-poly frying pan",
    "polygonal goblet",
    "small blocky treasure chest",
    "blocky treasure chest",
    "living vine staff",
    "vine staff",
    "crystal staff with frozen tip",
    "bone staff with floating skull",
)


def _strip_weapons_and_items(text: str) -> str:
    out = text
    for pat in _WEAPON_ITEM_RES:
        out = pat.sub("", out)
    for phrase in _WEAPON_ITEM_PHRASES:
        out = re.sub(re.escape(phrase), "", out, flags=re.I)
    return out

# Per-id subject overrides (short subject-only text).
_SUBJECT_OVERRIDES: dict[str, str] = {
    "archer_ranger": (
        "feral wild cat, rugged primitive survivor, simple ragged cloth tunic and wraps, "
        "rustic patched outfit, no bow, no quiver, no weapons"
    ),
    "bee": (
        "bee cat, angular blocky bee body, yellow-black striped, "
        "flat polygonal bee wings, small stinger, "
        "cat face, cat eyes, cat ears, chunky geometric shapes, not round"
    ),
    "red_slime": "red slime cat, round plush blob body, cat face, cat eyes, cat ears, small cat tail",
    "yellow_slime": "yellow slime cat, round plush blob body, cat face, cat eyes, cat ears, small cat tail",
    "larva_grub": (
        "larva grub cat, fat segmented cream grub body, cat face, cat ears, "
        "tiny insect legs under head, "
        f"{FELINE_EYE_LOCK}"
    ),
    "worm": (
        "cat worm hybrid, pink segmented low-poly worm body, cat head on front, "
        "cat ears, whiskers, no legs, upright coiled stance, "
        f"{FELINE_EYE_LOCK}"
    ),
    "alchemist": (
        "anthropomorphic cat alchemist, small blocky rectangular glasses, stained apron, "
        f"{FELINE_EYE_LOCK}"
    ),
}


def normalize_prompt_body(raw: str, *, entry_id: str | None = None) -> str:
    """Keep LoRA prefix + subject; drop redundant style tokens."""
    if entry_id and entry_id in _SUBJECT_OVERRIDES:
        subject = _SUBJECT_OVERRIDES[entry_id]
        return (
            f"{GENERATION_PROMPT_PREFIX} {subject}, {CHARACTER_BODY}, "
            f"{PROMPT_FRAMING}, {STYLE_LOCK}"
        )

    line = raw.strip()
    line = re.sub(r"<lora:[^>]+>\s*", "", line, flags=re.I)
    for phrase in _STRIP_PHRASES:
        line = re.sub(re.escape(phrase), "", line, flags=re.I)
    line = _strip_weapons_and_items(line)
    line = re.sub(r",?\s*T-pose\s*,?", ",", line, flags=re.I)
    line = re.sub(r",\s*glowing\s*,", ",", line, flags=re.I)
    line = re.sub(r",\s*glowing\s*$", "", line, flags=re.I)
    line = re.sub(r"\s+", " ", line).strip(" ,")

    low = line.lower()
    if "hand-painted textures" not in low:
        line = f"{line}, {CHARACTER_BODY}" if line else CHARACTER_BODY
    if "feline cat eyes" not in low:
        line = f"{line}, {FELINE_EYE_LOCK}" if line else FELINE_EYE_LOCK

    framing = f"{PROMPT_FRAMING}, {STYLE_LOCK}"
    return f"{GENERATION_PROMPT_PREFIX} {line}, {framing}" if line else f"{GENERATION_PROMPT_PREFIX} {framing}"


_TITLE_RE = re.compile(
    r"^\s*(?P<label>.+?)\s*(?:\((?P<en>[^)]+)\))?\s*:?\s*$"
)
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def _slug(text: str) -> str:
    s = text.lower().strip()
    s = s.replace("/", " ").replace("&", " and ")
    s = _NON_ALNUM.sub("_", s).strip("_")
    # keep short but readable
    parts = [p for p in s.split("_") if p and p not in {"cat", "the", "a", "an"}]
    if not parts:
        parts = [p for p in s.split("_") if p]
    return "_".join(parts[:6]) or "entry"


def _id_from_title(title: str, used: set[str]) -> str:
    m = _TITLE_RE.match(title.rstrip(":").strip())
    if m and m.group("en"):
        base = _slug(m.group("en"))
    elif m:
        base = _slug(m.group("label"))
    else:
        base = _slug(title)
    # common cleanup: "mage_with_staff" etc. already fine
    candidate = base
    n = 2
    while candidate in used:
        candidate = f"{base}_{n}"
        n += 1
    used.add(candidate)
    return candidate


def _id_from_prompt(prompt: str, used: set[str]) -> str:
    # known orphan prompts without a title line
    low = prompt.lower()
    for needle, nice_id in (
        ("goblin cat", "goblin"),
    ):
        if needle in low:
            candidate = nice_id
            n = 2
            while candidate in used:
                candidate = f"{nice_id}_{n}"
                n += 1
            used.add(candidate)
            return candidate

    # fallback: pick distinctive tokens after style prefix
    body = prompt
    if "ningraphix," in body:
        body = body.split("ningraphix,", 1)[1]
    # take first ~6 content words
    words = re.findall(r"[a-zA-Z0-9]+", body.lower())
    skip = {
        "ps1",
        "game",
        "screenshot",
        "anthropomorphic",
        "cat",
        "hybrid",
        "low",
        "poly",
        "chibi",
        "proportions",
        "big",
        "angular",
        "head",
        "mesh",
        "flat",
        "shaded",
        "crisp",
        "hard",
        "edges",
        "t",
        "pose",
        "neutral",
        "solid",
        "light",
        "grey",
        "background",
        "holding",
        "wearing",
        "with",
        "and",
        "a",
        "the",
        "of",
        "on",
        "in",
    }
    picked = [w for w in words if w not in skip][:5]
    base = "_".join(picked) if picked else "orphan"
    candidate = base
    n = 2
    while candidate in used:
        candidate = f"{base}_{n}"
        n += 1
    used.add(candidate)
    return candidate


def parse_prompts_txt(path: Path) -> list[dict[str, Any]]:
    """Return base entries: id, title, prompt, category."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    used: set[str] = set()
    entries: list[dict[str, Any]] = []
    pending_title: str | None = None

    section = "general"

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        # Subject-only line after "Title:" (no lora tag in txt)
        if (
            pending_title
            and "<lora:" not in line
            and not (line.endswith(":") and ("(" in line or len(line) < 80))
        ):
            title = pending_title
            pending_title = None
            entry_id = _id_from_title(title, used)
            display = title.rstrip(":").strip()
            entries.append(
                {
                    "id": entry_id,
                    "title": display,
                    "prompt": normalize_prompt_body(line, entry_id=entry_id),
                    "category": section,
                    "monster_id": entry_id,
                    "variant": "base",
                }
            )
            continue

        if "<lora:" in line:
            title = pending_title
            pending_title = None
            if title:
                entry_id = _id_from_title(title, used)
                display = title.rstrip(":").strip()
            else:
                entry_id = _id_from_prompt(line, used)
                display = entry_id
            entries.append(
                {
                    "id": entry_id,
                    "title": display,
                    "prompt": normalize_prompt_body(line, entry_id=entry_id),
                    "category": section,
                    "monster_id": entry_id,
                    "variant": "base",
                }
            )
            continue

        # section headers without English paren and without colon-only prompt titles
        if line.endswith(":") and "(" not in line and len(line) < 80:
            # e.g. "Классы (с разным фокусом..." already has paren — handled below
            label = line.rstrip(":").strip()
            if label and "<lora:" not in label:
                # If it looks like a character title (has Russian/English name pattern), keep as pending
                if any(c.isalpha() for c in label):
                    # Distinguish section vs character: short section-like lines without equipment words
                    pending_title = label
            continue

        # Character title lines: "Name (English):" or "Name:"
        if ("(" in line and ")" in line) or line.endswith(":"):
            pending_title = line.rstrip(":").strip()
            # Update section loosely from first word groups
            low = pending_title.lower()
            if "класс" in low or "class" in low:
                section = "class"
            elif "ракурс" in low or "view" in low or "поза" in low or "pose" in low:
                section = "pose"
            else:
                section = "creature"
            continue

        # Bare section header without colon
        if "<lora:" not in line and len(line) < 60 and not line.endswith(":"):
            section = _slug(line) or "general"

    return entries


def expand_variants(base: list[dict[str, Any]], variants: int) -> list[dict[str, Any]]:
    """Duplicate each base prompt into N seed slots (id_v2, id_v3, …)."""
    if variants < 1:
        raise ValueError("variants must be >= 1")
    if variants == 1:
        return [dict(e) for e in base]

    out: list[dict[str, Any]] = []
    for e in base:
        for i in range(1, variants + 1):
            row = dict(e)
            if i == 1:
                row["variant"] = "seed_1"
            else:
                row["id"] = f"{e['id']}_v{i}"
                row["variant"] = f"seed_{i}"
                row["monster_id"] = e["id"]
            out.append(row)
    return out


def write_prompt_pack_from_txt(
    txt_path: Path,
    out_path: Path,
    *,
    variants: int = 2,
    trigger: str = "gf_lowpoly",
) -> list[dict[str, Any]]:
    from style import STYLE_NEGATIVE  # local import

    base = parse_prompts_txt(txt_path)
    pack = expand_variants(base, variants)
    payload = {
        "version": 2,
        "count": len(pack),
        "base_count": len(base),
        "variants_per_prompt": variants,
        "source": str(txt_path.name),
        "trigger_word_suggestion": trigger,
        "negative_prompt": STYLE_NEGATIVE,
        "entries": pack,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        __import__("json").dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return pack


DEFAULT_LORA_PREFIX = f"{GENERATION_PROMPT_PREFIX} "


def append_prompt_to_txt(
    txt_path: Path,
    *,
    title: str,
    prompt_body: str,
) -> dict[str, Any]:
    """Append a titled prompt block to promts-for-generate.txt (mtime triggers auto rebuild)."""
    title = title.strip().rstrip(":")
    body = prompt_body.strip()
    if not body:
        raise ValueError("prompt required")
    if not title:
        raise ValueError("title required")

    existing = parse_prompts_txt(txt_path) if txt_path.is_file() else []
    used = {str(e["id"]) for e in existing}
    entry_id = _id_from_title(title, used)

    # Store subject-only in txt; normalization runs on parse/build.
    if "<lora:" in body:
        body = re.sub(r"<lora:[^>]+>\s*", "", body)
        for phrase in _STRIP_PHRASES:
            body = body.replace(phrase, "")
        body = re.sub(r"\s+", " ", body).strip(" ,")

    block = f"\n{title}:\n{body}\n"
    with txt_path.open("a", encoding="utf-8") as f:
        f.write(block)

    final = normalize_prompt_body(body, entry_id=entry_id)
    return {"id": entry_id, "title": title, "prompt": final}


if __name__ == "__main__":
    import json

    src = _ROOT / "promts-for-generate.txt"
    entries = parse_prompts_txt(src)
    print(json.dumps({"count": len(entries), "ids": [e["id"] for e in entries]}, ensure_ascii=False, indent=2))
