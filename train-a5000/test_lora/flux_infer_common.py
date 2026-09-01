"""Shared FLUX + LoRA loading for test_lora scripts."""

from __future__ import annotations

from pathlib import Path

import torch
from diffusers import FluxPipeline

# FLUX.1-dev bf16 in diffusers does not fit fully on 24GB (4090/A5000).
# Default: sequential_cpu_offload (~15-25 s/img). Use Forge for ~5-7 s/img.


def _apply_vram_mode(pipe: FluxPipeline, mode: str) -> None:
    mode = (mode or "sequential").strip().lower()
    if mode in ("fast", "cuda", "gpu"):
        print("VRAM mode: full GPU (needs ~32GB+ for FLUX bf16; 4090 may OOM)", flush=True)
        pipe.to("cuda")
        return
    if mode in ("offload", "low-vram", "low_vram", "cpu"):
        print("VRAM mode: model_cpu_offload (slow, safest)", flush=True)
        pipe.enable_model_cpu_offload()
        return
    print("VRAM mode: sequential_cpu_offload (24GB default)", flush=True)
    pipe.enable_sequential_cpu_offload()


def load_flux_with_lora(
    lora: Path,
    *,
    weight: float,
    hf_cache: Path,
    vram_mode: str = "sequential",
    fuse_lora: bool = True,
) -> FluxPipeline:
    print("Loading FLUX.1-dev (from HF cache if present)...", flush=True)
    pipe = FluxPipeline.from_pretrained(
        "black-forest-labs/FLUX.1-dev",
        torch_dtype=torch.bfloat16,
        cache_dir=str(hf_cache / "hub"),
    )
    _apply_vram_mode(pipe, vram_mode)

    print(f"Loading LoRA {lora} weight={weight}", flush=True)
    pipe.load_lora_weights(str(lora.parent), weight_name=lora.name)
    if fuse_lora:
        try:
            pipe.fuse_lora(lora_scale=weight)
        except Exception:
            try:
                pipe.set_adapters(["default"], adapter_weights=[weight])
            except Exception as exc:
                print(f"warn: could not set lora scale ({exc})", flush=True)
    else:
        try:
            pipe.set_adapters(["default"], adapter_weights=[weight])
        except Exception as exc:
            print(f"warn: unfused lora adapters ({exc})", flush=True)
    return pipe
