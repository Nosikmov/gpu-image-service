#!/usr/bin/env python3
"""Generate a fixed test grid for gf_lowpoly via Forge (A1111) txt2img API.

Usage (Forge must be running with --api):
  python test_gf_lowpoly.py
  FORGE_URL=http://127.0.0.1:7860 LORA_WEIGHT=0.85 python test_gf_lowpoly.py

On a rented GPU box: install/start Forge with Flux + put gf_lowpoly.safetensors
into models/Lora/, then run this script. Outputs go to ./out/
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_CFG = ROOT / "test_prompts.json"
OUT_DIR = ROOT / "out"


def http_json(method: str, url: str, body: dict | None = None, timeout: float = 300) -> Any:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def wait_forge(forge: str, max_wait_s: float = 900) -> None:
    deadline = time.time() + max_wait_s
    while time.time() < deadline:
        try:
            http_json("GET", f"{forge}/sdapi/v1/options", timeout=10)
            print(f"[ok] Forge API {forge}", flush=True)
            return
        except Exception:
            print(f"[wait] Forge not ready at {forge} ...", flush=True)
            time.sleep(5)
    raise SystemExit(f"Forge API unavailable: {forge}")


def build_prompt(subject: str, *, lora: str, weight: float, trigger: str) -> str:
    style = (
        "ningraphix, ps1 game screenshot, extremely low-poly, very few polygons, chunky blocky mesh, large flat facets, minimal geometric detail, PS1 N64 game asset, flat shaded, hard silhouette edges, no smooth subdivision, no high-poly sculpt, "
        "chibi proportions, big angular head, feline cat eyes, identical paired low-poly cat eyes, "
        "two matching oval eyes, flat white sclera, same size simple black round pupils, "
        "symmetrical, no mismatched eyes"
    )
    return f"<lora:{lora}:{weight}>, {trigger}, {style}, {subject}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Test gf_lowpoly LoRA via Forge API")
    ap.add_argument("--config", type=Path, default=DEFAULT_CFG)
    ap.add_argument("--forge", default=os.environ.get("FORGE_URL", "http://127.0.0.1:7860"))
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    ap.add_argument("--weight", type=float, default=None, help="LoRA strength override")
    ap.add_argument("--limit", type=int, default=0, help="Max images (0=all)")
    args = ap.parse_args()

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    forge = str(args.forge).rstrip("/")
    lora = str(cfg.get("lora") or "gf_lowpoly")
    weight = float(args.weight if args.weight is not None else cfg.get("lora_weight") or 0.85)
    trigger = str(cfg.get("trigger") or "gf_lowpoly")
    prompts = list(cfg.get("prompts") or [])
    if args.limit and args.limit > 0:
        prompts = prompts[: args.limit]

    wait_forge(forge)

    opts = {
        "sd_model_checkpoint": str(cfg.get("model") or "flux1-dev-Q6_K.gguf"),
        "forge_unet_storage_dtype": str(
            cfg.get("unet_storage_dtype") or "Automatic (fp16 LoRA)"
        ),
    }
    try:
        http_json("POST", f"{forge}/sdapi/v1/options", opts, timeout=180)
        print(f"[forge] options: {opts}", flush=True)
    except Exception as exc:
        print(f"[forge] options warn: {exc}", flush=True)

    args.out.mkdir(parents=True, exist_ok=True)
    seed_base = int(cfg.get("seed_base") or 42)
    manifest = []

    for i, subject in enumerate(prompts):
        seed = seed_base + i
        prompt = build_prompt(subject, lora=lora, weight=weight, trigger=trigger)
        body = {
            "prompt": prompt,
            "negative_prompt": "",
            "width": int(cfg.get("width") or 512),
            "height": int(cfg.get("height") or 512),
            "steps": int(cfg.get("steps") or 20),
            "sampler_name": str(cfg.get("sampler_name") or "Euler"),
            "scheduler": str(cfg.get("scheduler") or "Simple"),
            "cfg_scale": float(cfg.get("cfg_scale") or 1.0),
            "distilled_cfg_scale": float(cfg.get("distilled_cfg_scale") or 3.5),
            "seed": seed,
            "batch_size": 1,
            "n_iter": 1,
        }
        print(f"[{i+1}/{len(prompts)}] seed={seed} {subject[:60]}...", flush=True)
        t0 = time.time()
        try:
            res = http_json("POST", f"{forge}/sdapi/v1/txt2img", body, timeout=600)
        except Exception as exc:
            print(f"  FAIL: {exc}", flush=True)
            manifest.append({"index": i, "ok": False, "error": str(exc), "prompt": prompt})
            continue
        images = res.get("images") or []
        if not images:
            print("  FAIL: no images in response", flush=True)
            manifest.append({"index": i, "ok": False, "error": "empty", "prompt": prompt})
            continue
        raw = images[0]
        if "," in raw[:64]:
            raw = raw.split(",", 1)[1]
        png = base64.b64decode(raw)
        name = f"{i+1:02d}_seed{seed}.png"
        path = args.out / name
        path.write_bytes(png)
        elapsed = time.time() - t0
        print(f"  -> {path.name} ({len(png)} bytes, {elapsed:.1f}s)", flush=True)
        manifest.append(
            {
                "index": i,
                "ok": True,
                "file": name,
                "seed": seed,
                "prompt": prompt,
                "seconds": round(elapsed, 2),
            }
        )

    man_path = args.out / "manifest.json"
    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ok = sum(1 for m in manifest if m.get("ok"))
    print(f"Done: {ok}/{len(prompts)} -> {args.out}", flush=True)
    return 0 if ok == len(prompts) else 1


if __name__ == "__main__":
    raise SystemExit(main())
