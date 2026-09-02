#!/usr/bin/env python3
"""Download Flux fp8 + text encoders for Forge on Linux GPU server."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from huggingface_hub import hf_hub_download

FORGE = Path(os.environ.get("FORGE_DIR", "/home/sdforge/stable-diffusion-webui-forge"))

DOWNLOADS: tuple[tuple[str, str, Path, int], ...] = (
    (
        "Comfy-Org/flux1-dev",
        "flux1-dev-fp8.safetensors",
        FORGE / "models" / "Stable-diffusion" / "flux1-dev-fp8.safetensors",
        17_200_000_000,
    ),
    (
        "comfyanonymous/flux_text_encoders",
        "clip_l.safetensors",
        FORGE / "models" / "text_encoder" / "clip_l.safetensors",
        240_000_000,
    ),
    (
        "comfyanonymous/flux_text_encoders",
        "t5xxl_fp8_e4m3fn.safetensors",
        FORGE / "models" / "text_encoder" / "t5xxl_fp8_e4m3fn.safetensors",
        4_800_000_000,
    ),
)


def _ok(path: Path, min_bytes: int) -> bool:
    return path.is_file() and path.stat().st_size >= min_bytes


def main() -> int:
    FORGE.mkdir(parents=True, exist_ok=True)
    for _, _, dst, _ in DOWNLOADS:
        dst.parent.mkdir(parents=True, exist_ok=True)

    for repo, fname, dst, min_bytes in DOWNLOADS:
        if _ok(dst, min_bytes):
            size_gb = dst.stat().st_size / 1e9
            print(f"[skip] {dst.name} OK ({size_gb:.2f} GB)")
            continue

        if dst.is_file() and dst.stat().st_size < min_bytes:
            partial = dst.stat().st_size / 1e9
            print(f"[resume] {dst.name} partial {partial:.2f} GB -> {repo}/{fname}")
        else:
            print(f"[download] {repo}/{fname} -> {dst}")

        cached = hf_hub_download(
            repo,
            fname,
            local_dir=str(dst.parent),
            local_dir_use_symlinks=False,
            resume_download=True,
        )
        cached_path = Path(cached)
        if cached_path.resolve() != dst.resolve():
            cached_path.replace(dst)
        size_gb = dst.stat().st_size / 1e9
        print(f"[done] {dst.name} ({size_gb:.2f} GB)")

    print("All Forge Flux models ready.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
