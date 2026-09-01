#!/usr/bin/env python3
"""Regenerate lora-curation/prompts.json from promts-for-generate.txt."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from parse_prompts_txt import write_prompt_pack_from_txt  # noqa: E402
from style import TRIGGER_WORD  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build prompts.json for Forge Flux curation")
    parser.add_argument(
        "--txt",
        type=Path,
        default=_ROOT / "promts-for-generate.txt",
        help="Source prompts text file",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=_ROOT / "prompts.json",
        help="Output prompts.json path",
    )
    parser.add_argument(
        "--variants",
        type=int,
        default=1,
        help="Seed slots per prompt (1 => 40 candidates from 40 bases)",
    )
    parser.add_argument(
        "--trigger",
        default=TRIGGER_WORD,
        help="Suggested LoRA trigger word for export captions",
    )
    args = parser.parse_args()

    if not args.txt.is_file():
        print(f"Missing prompts file: {args.txt}", file=sys.stderr)
        return 1

    pack = write_prompt_pack_from_txt(
        args.txt,
        args.out,
        variants=args.variants,
        trigger=args.trigger,
    )
    print(f"Wrote {len(pack)} prompts to {args.out} (variants={args.variants})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
