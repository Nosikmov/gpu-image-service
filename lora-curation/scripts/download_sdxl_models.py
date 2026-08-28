#!/usr/bin/env python3
"""Download SDXL checkpoint + dual LoRA slots for Forge curation."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from huggingface_hub import hf_hub_download

FORGE = Path(r"F:\fluxGenerationForLora\stable-diffusion-webui-forge")
SD_DIR = FORGE / "models" / "Stable-diffusion"
LORA_DIR = FORGE / "models" / "Lora"


def main() -> int:
    SD_DIR.mkdir(parents=True, exist_ok=True)
    LORA_DIR.mkdir(parents=True, exist_ok=True)

    ckpt = SD_DIR / "sd_xl_base_1.0.safetensors"
    if not ckpt.exists() or ckpt.stat().st_size < 1_000_000_000:
        print("Downloading SDXL base (~6.5 GB)...")
        hf_hub_download(
            "stabilityai/stable-diffusion-xl-base-1.0",
            "sd_xl_base_1.0.safetensors",
            local_dir=str(SD_DIR),
        )
    else:
        print(f"SDXL base OK ({ckpt.stat().st_size / 1e9:.2f} GB)")

    lpp = LORA_DIR / "Low_Poly_Papercraft.safetensors"
    if not lpp.exists():
        print("Downloading PS1 Graphics SDXL LoRA -> Low_Poly_Papercraft slot...")
        path = hf_hub_download("veryVANYA/ps1-graphics-sdxl", "ps1_style_SDXL_v1.safetensors")
        shutil.copy2(path, lpp)
    else:
        print("Low_Poly_Papercraft slot OK")

    ning = LORA_DIR / "ningraphix.safetensors"
    if not ning.exists():
        print("Downloading PS1Redmond SDXL LoRA -> ningraphix slot...")
        path = hf_hub_download(
            "artificialguybr/ps1redmond-ps1-game-graphics-lora-for-sdxl",
            "PS1Redmond-PS1Game-Playstation1Graphics.safetensors",
        )
        shutil.copy2(path, ning)
    else:
        print("ningraphix slot OK")

    print("Done.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
