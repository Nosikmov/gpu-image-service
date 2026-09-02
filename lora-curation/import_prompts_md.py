#!/usr/bin/env python3
"""Import GF Lowpoly PS1 markdown prompts -> prompts.json (full prompts, no re-normalize)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from style import STYLE_NEGATIVE  # noqa: E402

_CHAR_RE = re.compile(r"^##\s*(?P<num>\d+)\s*[—\-]\s*(?P<name>.+?)\s*$")
_VARIANT_RE = re.compile(r"^###\s*Variant\s*(?P<n>\d+)\s*$", re.I)
_LORA_FIX_RE = re.compile(r"\[lora:ningraphix(?::[\d.]+)?\]", re.I)
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def _slug(name: str) -> str:
    s = _NON_ALNUM.sub("_", name.lower()).strip("_")
    parts = [p for p in s.split("_") if p and p not in {"cat", "the", "a", "an"}]
    return "_".join(parts[:6]) or "entry"


def _fix_lora(prompt: str) -> str:
    return _LORA_FIX_RE.sub("<lora:ningraphix-000031:0.9>", prompt)


def parse_md_prompts(md_path: Path, *, only_variant: int | None = None) -> list[dict]:
    entries: list[dict] = []
    char_title: str | None = None
    char_slug: str | None = None
    variant_n: int | None = None
    single_prompt = False

    for raw in md_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line == "---":
            continue

        m_char = _CHAR_RE.match(line)
        if m_char:
            char_title = m_char.group("name").strip()
            char_slug = _slug(char_title)
            variant_n = None
            single_prompt = False
            continue

        m_var = _VARIANT_RE.match(line)
        if m_var and char_title and char_slug:
            variant_n = int(m_var.group("n"))
            continue

        if char_slug and char_title and not line.startswith("#"):
            if variant_n is None:
                # Single canonical prompt block (no Variant header)
                single_prompt = True
                use_variant = 1
            else:
                use_variant = variant_n
                if only_variant is not None and use_variant != only_variant:
                    variant_n = None
                    continue

            entry_id = char_slug
            used = {e["id"] for e in entries}
            if entry_id in used:
                entry_id = f"{char_slug}_v{use_variant}"
            prompt = _fix_lora(line)
            title = char_title if single_prompt or only_variant else f"{char_title} (Variant {use_variant})"
            entries.append(
                {
                    "id": entry_id,
                    "title": title,
                    "prompt": prompt,
                    "category": "creature",
                    "monster_id": char_slug,
                    "variant": "canonical" if single_prompt or only_variant else f"v{use_variant}",
                }
            )
            variant_n = None

    return entries


def write_prompts_json(entries: list[dict], out_path: Path, *, source: str) -> None:
    payload = {
        "version": 3,
        "count": len(entries),
        "base_count": len({e["monster_id"] for e in entries}),
        "variants_per_prompt": max(
            sum(1 for e in entries if e["monster_id"] == mid)
            for mid in {e["monster_id"] for e in entries}
        )
        if entries
        else 1,
        "source": source,
        "trigger_word_suggestion": "gf_lowpoly",
        "negative_prompt": STYLE_NEGATIVE,
        "entries": entries,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Import GF Lowpoly PS1 markdown prompts")
    parser.add_argument(
        "md",
        type=Path,
        nargs="?",
        default=_ROOT / "GF Lowpoly PS1 — Character Generation Prompts.md",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=_ROOT / "prompts.json",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--only-variant",
        type=int,
        default=2,
        help="Use only this variant number (default: 2). Pass 0 to import all variants.",
    )
    args = parser.parse_args()

    if not args.md.is_file():
        print(f"Missing file: {args.md}", file=sys.stderr)
        return 1

    only_variant = None if args.only_variant == 0 else args.only_variant
    entries = parse_md_prompts(args.md, only_variant=only_variant)
    if not entries:
        print("No prompts parsed.", file=sys.stderr)
        return 1

    print(f"Parsed {len(entries)} prompts from {args.md.name}")
    for e in entries[:5]:
        print(f"  {e['id']:20} {e['title'][:50]}")
    if len(entries) > 5:
        print(f"  ... +{len(entries) - 5} more")

    if args.dry_run:
        return 0

    write_prompts_json(entries, args.out, source=args.md.name)
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
