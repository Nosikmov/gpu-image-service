#!/usr/bin/env python3
"""Generate test images for every prompt in lora-curation/prompts.json (dataset v2).

Uses the same venv + HF cache as training. No Forge required.

  cd ~/gpu-image-service/train-a5000/test_lora
  ./run_dataset_test.sh
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TRAIN_ROOT = ROOT.parent
REPO_ROOT = TRAIN_ROOT.parent
LORA_CURATION = REPO_ROOT / "lora-curation"
DEFAULT_PROMPTS = LORA_CURATION / "prompts.json"
DEFAULT_LORA = TRAIN_ROOT / "output" / "gf_lowpoly" / "gf_lowpoly.safetensors"
DEFAULT_OUT = ROOT / "out_dataset"
DEFAULT_HF = TRAIN_ROOT / ".hf-cache"

if str(LORA_CURATION) not in sys.path:
    sys.path.insert(0, str(LORA_CURATION))

from caption_train import default_negative_prompt, prompt_for_inference  # noqa: E402
from flux_infer_common import load_flux_with_lora  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Test gf_lowpoly on all curation prompts")
    ap.add_argument("--prompts", type=Path, default=DEFAULT_PROMPTS)
    ap.add_argument("--lora", type=Path, default=DEFAULT_LORA)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--weight", type=float, default=0.9)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--seed-base", type=int, default=1000)
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--guidance", type=float, default=3.5)
    ap.add_argument("--negative", default="", help="Override negative prompt (default: from prompts.json)")
    ap.add_argument("--no-negative", action="store_true")
    ap.add_argument(
        "--vram-mode",
        choices=("sequential", "offload", "fast"),
        default="sequential",
        help="sequential=24GB default; offload=slowest; fast=full GPU (may OOM)",
    )
    ap.add_argument("--low-vram", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args()
    if args.low_vram:
        args.vram_mode = "offload"

    os.environ.setdefault("HF_HOME", str(DEFAULT_HF))
    os.environ.setdefault("HF_HUB_CACHE", str(DEFAULT_HF / "hub"))
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "0")
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

    if not args.prompts.is_file():
        print(f"Missing prompts: {args.prompts}", file=sys.stderr)
        return 1
    if not args.lora.is_file():
        print(f"Missing LoRA: {args.lora}", file=sys.stderr)
        return 1

    pack = json.loads(args.prompts.read_text(encoding="utf-8"))
    entries = list(pack.get("entries") or [])
    if args.limit > 0:
        entries = entries[: args.limit]

    negative = ""
    if not args.no_negative:
        negative = args.negative or str(pack.get("negative_prompt") or "") or default_negative_prompt()

    import torch

    pipe = load_flux_with_lora(
        args.lora,
        weight=args.weight,
        hf_cache=DEFAULT_HF,
        vram_mode=args.vram_mode,
        fuse_lora=(args.vram_mode == "fast"),
    )

    print(f"Prompts: {args.prompts} ({len(entries)} entries)", flush=True)
    if negative:
        print(f"Negative: {negative[:80]}...", flush=True)

    args.out.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []

    for i, row in enumerate(entries):
        entry_id = str(row.get("id") or f"entry_{i}")
        prompt = prompt_for_inference(str(row.get("prompt") or ""), entry_id=entry_id)
        if not prompt:
            print(f"[skip] {entry_id}: empty prompt", flush=True)
            continue
        seed = args.seed_base + i
        out_path = args.out / f"{entry_id}.png"
        print(f"[{i+1}/{len(entries)}] {entry_id} seed={seed}", flush=True)
        gen = torch.Generator(device="cpu").manual_seed(seed)
        kwargs = dict(
            prompt=prompt,
            num_inference_steps=args.steps,
            guidance_scale=args.guidance,
            width=512,
            height=512,
            generator=gen,
        )
        if negative:
            kwargs["negative_prompt"] = negative
        image = pipe(**kwargs).images[0]
        image.save(out_path)
        print(f"  -> {out_path}", flush=True)
        manifest.append({"id": entry_id, "file": out_path.name, "seed": seed, "prompt": prompt})

    (args.out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Done {len(manifest)} images -> {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
