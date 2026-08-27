#!/usr/bin/env python3
"""Generate 12 test images for gf_lowpoly using the Ostris/ai-toolkit venv + HF FLUX cache.

No Forge required. Intended for the rented GPU box right after training:

  cd ~/gpu-image-service/train-a5000/test_lora
  chmod +x run_on_server.sh
  ./run_on_server.sh

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
DEFAULT_CFG = ROOT / "test_prompts.json"
DEFAULT_LORA = TRAIN_ROOT / "output" / "gf_lowpoly" / "gf_lowpoly.safetensors"
DEFAULT_OUT = ROOT / "out"
DEFAULT_HF = TRAIN_ROOT / ".hf-cache"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, default=DEFAULT_CFG)
    ap.add_argument("--lora", type=Path, default=DEFAULT_LORA)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--weight", type=float, default=0.85)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

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

    import torch
    from diffusers import FluxPipeline

    print("Loading FLUX.1-dev (from HF cache if present)...", flush=True)
    pipe = FluxPipeline.from_pretrained(
        "black-forest-labs/FLUX.1-dev",
        torch_dtype=torch.bfloat16,
    )
    pipe.enable_model_cpu_offload()
    print(f"Loading LoRA {args.lora} weight={args.weight}", flush=True)
    pipe.load_lora_weights(str(args.lora.parent), weight_name=args.lora.name)
    try:
        pipe.fuse_lora(lora_scale=args.weight)
    except Exception:
        # older diffusers: scale via cross_attention_kwargs / set_adapters
        try:
            pipe.set_adapters(["default"], adapter_weights=[args.weight])
        except Exception as exc:
            print(f"warn: could not set lora scale ({exc})", flush=True)

    args.out.mkdir(parents=True, exist_ok=True)
    manifest = []
    style = (
        "ningraphix, ps1 game screenshot, low-poly mesh, flat shaded, crisp hard edges, "
        "chibi proportions, big angular head"
    )

    for i, subject in enumerate(subjects):
        seed = seed_base + i
        prompt = f"{trigger}, {style}, {subject}"
        print(f"[{i+1}/{len(subjects)}] seed={seed} {subject[:55]}...", flush=True)
        gen = torch.Generator(device="cpu").manual_seed(seed)
        image = pipe(
            prompt=prompt,
            num_inference_steps=steps,
            guidance_scale=guidance,
            width=width,
            height=height,
            generator=gen,
        ).images[0]
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
