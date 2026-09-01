#!/usr/bin/env python3
"""Generate test images via Forge fp8 API — all prompts from prompts.json."""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
LORA_CURATION = REPO / "lora-curation"
DEFAULT_PROMPTS = LORA_CURATION / "prompts.json"
DEFAULT_OUT = ROOT / "out_forge_dataset"
GEN_CFG = LORA_CURATION / "forge_gen.json"

if str(LORA_CURATION) not in sys.path:
    sys.path.insert(0, str(LORA_CURATION))

from caption_train import default_negative_prompt, prompt_for_inference  # noqa: E402
from style import TRIGGER_WORD  # noqa: E402


def http_json(method: str, url: str, body: dict | None = None, timeout: float = 600):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def wait_forge(forge: str) -> None:
    for _ in range(120):
        try:
            http_json("GET", f"{forge}/sdapi/v1/sd-models", timeout=10)
            return
        except Exception:
            time.sleep(5)
    raise SystemExit(f"Forge not ready: {forge}")


def forge_prompt(text: str, *, weight: float, mode: str) -> str:
    if mode == "bootstrap":
        tags = "<lora:lowpoly_flux:0.9> <lora:OOTN64_Krea2:0.9>"
    elif mode == "full":
        tags = f"<lora:gf_lowpoly:{weight}> <lora:lowpoly_flux:0.9> <lora:OOTN64_Krea2:0.9>"
    else:
        tags = f"<lora:gf_lowpoly:{weight}>"
    if text.lower().startswith(TRIGGER_WORD):
        return f"{tags}, {text}"
    return f"{tags}, {TRIGGER_WORD}, {text}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", type=Path, default=DEFAULT_PROMPTS)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--forge", default=os.environ.get("FORGE_URL", "http://127.0.0.1:7860"))
    ap.add_argument("--weight", type=float, default=0.9)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--mode", choices=("trained", "bootstrap", "full"), default="trained")
    ap.add_argument("--seed-base", type=int, default=2000)
    args = ap.parse_args()

    forge = args.forge.rstrip("/")
    gen = json.loads(GEN_CFG.read_text(encoding="utf-8")) if GEN_CFG.is_file() else {}
    pack = json.loads(args.prompts.read_text(encoding="utf-8"))
    entries = list(pack.get("entries") or [])
    if args.limit > 0:
        entries = entries[: args.limit]
    negative = str(pack.get("negative_prompt") or "") or default_negative_prompt()

    wait_forge(forge)
    opts = {
        "sd_model_checkpoint": str(gen.get("model") or "flux1-dev-fp8.safetensors"),
        "forge_unet_storage_dtype": str(gen.get("unet_storage_dtype") or "Automatic (fp16 LoRA)"),
    }
    try:
        http_json("POST", f"{forge}/sdapi/v1/options", opts, timeout=180)
    except Exception as exc:
        print(f"options warn: {exc}", flush=True)

    args.out.mkdir(parents=True, exist_ok=True)
    manifest = []

    for i, row in enumerate(entries):
        eid = str(row.get("id") or f"e{i}")
        cap = prompt_for_inference(str(row.get("prompt") or ""), entry_id=eid)
        prompt = forge_prompt(cap, weight=args.weight, mode=args.mode)
        seed = args.seed_base + i
        body = {
            "prompt": prompt,
            "negative_prompt": negative,
            "width": int(gen.get("width") or 512),
            "height": int(gen.get("height") or 512),
            "steps": int(gen.get("steps") or 20),
            "sampler_name": str(gen.get("sampler_name") or "Euler"),
            "scheduler": str(gen.get("scheduler") or "Simple"),
            "cfg_scale": float(gen.get("cfg_scale") or 1.0),
            "distilled_cfg_scale": float(gen.get("distilled_cfg_scale") or 3.5),
            "seed": seed,
            "batch_size": 1,
            "n_iter": 1,
        }
        print(f"[{i+1}/{len(entries)}] {eid} seed={seed}", flush=True)
        t0 = time.time()
        try:
            res = http_json("POST", f"{forge}/sdapi/v1/txt2img", body)
        except Exception as exc:
            print(f"  FAIL: {exc}", flush=True)
            continue
        imgs = res.get("images") or []
        if not imgs:
            print("  FAIL: empty", flush=True)
            continue
        raw = imgs[0]
        if "," in raw[:64]:
            raw = raw.split(",", 1)[1]
        path = args.out / f"{eid}.png"
        path.write_bytes(base64.b64decode(raw))
        sec = time.time() - t0
        print(f"  -> {path.name} ({sec:.1f}s)", flush=True)
        manifest.append({"id": eid, "file": path.name, "seed": seed, "seconds": sec, "prompt": prompt})

    (args.out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Done {len(manifest)} -> {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
