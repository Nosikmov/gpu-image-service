#!/usr/bin/env python3
"""Generate 12 test images for gf_lowpoly using the Ostris/ai-toolkit venv + HF FLUX cache.

No Forge required. Intended for the rented GPU box right after training:

  cd ~/gpu-image-service/train-a5000/test_lora
  ../cycle.sh test slow

Or:
  ../.ai-toolkit/.venv/bin/python infer_diffusers.py
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
DEFAULT_CFG = ROOT / "test_prompts.json"
DEFAULT_LORA = TRAIN_ROOT / "output" / "gf_lowpoly" / "gf_lowpoly.safetensors"
DEFAULT_OUT = ROOT / "out"
DEFAULT_HF = TRAIN_ROOT / ".hf-cache"

if str(LORA_CURATION) not in sys.path:
    sys.path.insert(0, str(LORA_CURATION))

from caption_train import default_negative_prompt  # noqa: E402
from flux_infer_common import load_flux_with_lora  # noqa: E402
from style import FELINE_EYE_LOCK  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, default=DEFAULT_CFG)
    ap.add_argument("--lora", type=Path, default=DEFAULT_LORA)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--weight", type=float, default=0.85)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument(
        "--vram-mode",
        choices=("sequential", "offload", "fast"),
        default="sequential",
        help="sequential=24GB default; offload=slowest; fast=full GPU (may OOM on 4090)",
    )
    ap.add_argument("--low-vram", action="store_true", help=argparse.SUPPRESS)  # legacy alias
    args = ap.parse_args()
    if args.low_vram:
        args.vram_mode = "offload"

    # Prefer training cache on the GPU box
    os.environ.setdefault("HF_HOME", str(DEFAULT_HF))
    os.environ.setdefault("HF_HUB_CACHE", str(DEFAULT_HF / "hub"))
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "0")
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

    if not args.lora.is_file():
        print(f"Missing LoRA: {args.lora}", file=sys.stderr)
        print("Copy gf_lowpoly.safetensors there or pass --lora PATH", file=sys.stderr)
        return 1

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    subjects = list(cfg.get("prompts") or [])
    if args.limit and args.limit > 0:
        subjects = subjects[: args.limit]
    trigger = str(cfg.get("trigger") or "gf_lowpoly")
    seed_base = int(cfg.get("seed_base") or 42)
    steps = int(cfg.get("steps") or 20)
    guidance = float(cfg.get("distilled_cfg_scale") or 3.5)
    width = int(cfg.get("width") or 512)
    height = int(cfg.get("height") or 512)
    negative = str(cfg.get("negative_prompt") or "") or default_negative_prompt()

    import torch

    pipe = load_flux_with_lora(
        args.lora,
        weight=args.weight,
        hf_cache=DEFAULT_HF,
        vram_mode=args.vram_mode,
        fuse_lora=(args.vram_mode == "fast"),
    )

    args.out.mkdir(parents=True, exist_ok=True)
    manifest = []
    style = (
        "ps1 game screenshot, extremely low-poly, chunky blocky mesh, large flat facets, "
        "PS1 N64 game asset, flat shaded, hard silhouette edges, chibi proportions, big angular head, "
        f"{FELINE_EYE_LOCK}"
    )

    for i, subject in enumerate(subjects):
        seed = seed_base + i
        prompt = f"{trigger}, {style}, {subject}"
        print(f"[{i+1}/{len(subjects)}] seed={seed} {subject[:55]}...", flush=True)
        gen = torch.Generator(device="cpu").manual_seed(seed)
        kwargs = dict(
            prompt=prompt,
            num_inference_steps=steps,
            guidance_scale=guidance,
            width=width,
            height=height,
            generator=gen,
        )
        if negative:
            kwargs["negative_prompt"] = negative
        image = pipe(**kwargs).images[0]
        name = f"{i+1:02d}_seed{seed}.png"
        path = args.out / name
        image.save(path)
        print(f"  -> {path}", flush=True)
        manifest.append({"index": i, "file": name, "seed": seed, "prompt": prompt})

    (args.out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Done {len(manifest)} images -> {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
