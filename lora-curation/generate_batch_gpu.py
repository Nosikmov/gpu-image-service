#!/usr/bin/env python3
"""Generate curation images via Forge (A1111) txt2img API — Flux + style LoRAs."""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import (  # noqa: E402
    IMAGES_DIR,
    find_image_rel,
    load_manifest,
    load_prompts,
    load_ratings,
    save_manifest,
    save_ratings,
)
from style import STYLE_NEGATIVE  # noqa: E402

DEFAULT_FORGE = "http://127.0.0.1:7860"
GEN_CONFIG_PATH = _ROOT / "forge_gen.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _forge_url() -> str:
    return (os.environ.get("FORGE_URL") or DEFAULT_FORGE).rstrip("/")


def _load_gen_config() -> dict[str, Any]:
    if GEN_CONFIG_PATH.is_file():
        return json.loads(GEN_CONFIG_PATH.read_text(encoding="utf-8"))
    return {
        "model": "flux1-dev-Q6_K.gguf",
        "width": 512,
        "height": 512,
        "steps": 20,
        "sampler_name": "Euler",
        "scheduler": "Simple",
        "cfg_scale": 1.0,
        "distilled_cfg_scale": 3.5,
        "seed": -1,
        "timeout_sec": 300,
    }


def _http_json(method: str, url: str, body: dict | None = None, timeout: float = 120) -> Any:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _forge_alive(forge: str, timeout: float = 10) -> bool:
    try:
        _http_json("GET", f"{forge}/sdapi/v1/sd-models", timeout=timeout)
        return True
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        try:
            _http_json("GET", f"{forge}/sdapi/v1/options", timeout=timeout)
            return True
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
            return False


def _wait_forge(forge: str, *, max_wait_s: float = 600, poll_s: float = 5) -> None:
    deadline = time.time() + max_wait_s
    while time.time() < deadline:
        if _forge_alive(forge):
            return
        try:
            print(f"[wait] Forge API not ready at {forge} ...", flush=True)
        except OSError:
            pass
        time.sleep(poll_s)
    raise SystemExit(
        f"Forge API unavailable: {forge}\n"
        f"Start WebUI with --api (webui-user.bat), wait for model load, then retry."
    )


def _ping_forge(forge: str, timeout: float = 30) -> None:
    if _forge_alive(forge, timeout=timeout):
        return
    _wait_forge(forge)


def _ensure_forge_options(forge: str, cfg: dict[str, Any]) -> None:
    """GGUF + LoRA requires Diffusion in Low Bits = Automatic (fp16 LoRA). Set once per batch."""
    body = {
        "sd_model_checkpoint": str(cfg.get("model") or "flux1-dev-Q6_K.gguf"),
        "forge_unet_storage_dtype": str(
            cfg.get("unet_storage_dtype") or "Automatic (fp16 LoRA)"
        ),
    }
    try:
        _http_json("POST", f"{forge}/sdapi/v1/options", body, timeout=120)
        print(f"[forge] options set: {body}", flush=True)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        print(f"[forge] options warn: {exc}", flush=True)


def _interrupt_forge(forge: str) -> None:
    for path in ("/sdapi/v1/interrupt", "/sdapi/v1/skip"):
        try:
            _http_json("POST", f"{forge}{path}", {}, timeout=10)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
            pass


def generate_one(
    forge: str,
    prompt: str,
    *,
    negative: str,
    out_path: Path,
    cfg: dict[str, Any],
    retries: int = 5,
) -> dict[str, Any]:
    timeout = float(cfg.get("timeout_sec") or 180)
    # Do NOT override checkpoint every call — reloading Flux mid-batch crashes Forge.
    payload = {
        "prompt": prompt,
        "negative_prompt": negative,
        "steps": int(cfg.get("steps", 20)),
        "sampler_name": str(cfg.get("sampler_name") or "Euler"),
        "scheduler": str(cfg.get("scheduler") or "Simple"),
        "cfg_scale": float(cfg.get("cfg_scale", 1.0)),
        "distilled_cfg_scale": float(cfg.get("distilled_cfg_scale", 3.5)),
        "width": int(cfg.get("width", 512)),
        "height": int(cfg.get("height", 512)),
        "seed": int(cfg.get("seed", -1)),
        "batch_size": 1,
        "n_iter": 1,
        "save_images": False,
        "send_images": True,
    }
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            _wait_forge(forge, max_wait_s=600)
            # Do NOT interrupt before a normal request — that destabilizes Forge
            # after 1-2 Flux gens (model unload mid-cycle -> hard exit).
            if attempt > 1:
                _interrupt_forge(forge)
                time.sleep(2)
            t0 = time.time()
            result = _http_json("POST", f"{forge}/sdapi/v1/txt2img", payload, timeout=timeout)
            images = result.get("images") or []
            if not images:
                raise RuntimeError("txt2img returned no images")
            raw_b64 = images[0]
            if "," in raw_b64[:64]:
                raw_b64 = raw_b64.split(",", 1)[1]
            blob = base64.b64decode(raw_b64)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(blob)

            info: dict[str, Any] = {}
            try:
                info = json.loads(result.get("info") or "{}")
            except json.JSONDecodeError:
                pass
            return {
                "bytes": out_path.stat().st_size,
                "seed": info.get("seed"),
                "elapsed_sec": round(time.time() - t0, 2),
                "model": cfg.get("model"),
                "attempt": attempt,
            }
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ConnectionError, OSError, RuntimeError) as exc:
            last_exc = exc
            print(f"[retry {attempt}/{retries}] {exc}", flush=True)
            _interrupt_forge(forge)
            time.sleep(min(10 * attempt, 60))
    assert last_exc is not None
    raise last_exc


def _delete_images(entry_id: str) -> None:
    for ext in (".png", ".webp", ".jpg", ".jpeg"):
        path = IMAGES_DIR / f"{entry_id}{ext}"
        if path.is_file():
            path.unlink()


def _clear_ratings(entry_ids: list[str]) -> None:
    """Remove ratings so regenerated images show as unset for re-review."""
    ratings = load_ratings()
    entries = ratings.setdefault("entries", {})
    changed = False
    for entry_id in entry_ids:
        if entry_id in entries:
            entries.pop(entry_id, None)
            changed = True
    if changed:
        ratings["updated_at"] = _utc_now()
        save_ratings(ratings)
        print(f"[ratings] cleared: {', '.join(entry_ids)}", flush=True)


def _ids_by_rating(wanted: set[str]) -> list[str]:
    ratings = load_ratings()
    out: list[str] = []
    for entry_id, row in (ratings.get("entries") or {}).items():
        if str(row.get("rating") or "") in wanted:
            out.append(str(entry_id))
    return out


def generate_batch_forge(
    *,
    limit: int | None,
    skip_existing: bool,
    continue_on_error: bool,
    delay_s: float,
    ids: list[str] | None,
    rejected_only: bool = False,
    include_maybe: bool = False,
) -> dict[str, int]:
    forge = _forge_url()
    cfg = _load_gen_config()
    print(f"Forge: {forge}")
    print(f"Config: {json.dumps(cfg, ensure_ascii=False)}")
    _ping_forge(forge)
    _ensure_forge_options(forge, cfg)

    pack = load_prompts()
    entries = pack["entries"]

    if rejected_only:
        wanted = {"reject", "maybe"} if include_maybe else {"reject"}
        id_set = set(_ids_by_rating(wanted))
        if not id_set:
            print("No rejected entries to regenerate.")
            return {"ok": 0, "skipped": 0, "failed": 0, "total": 0}
        entries = [e for e in entries if e["id"] in id_set]
        # Force redo: drop old files + ratings so they show as unset in reviewer
        redo_ids = [str(e["id"]) for e in entries]
        print(f"Regenerating {len(redo_ids)} rejected: {', '.join(redo_ids)}")
        for entry_id in redo_ids:
            _delete_images(entry_id)
        _clear_ratings(redo_ids)
        skip_existing = False
    elif ids:
        id_set = set(ids)
        entries = [e for e in entries if e["id"] in id_set]

    if limit is not None:
        entries = entries[:limit]

    negative = str(pack.get("negative_prompt") if pack.get("negative_prompt") is not None else STYLE_NEGATIVE)

    manifest = load_manifest()
    manifest.setdefault("version", 1)
    manifest["generator"] = "forge-flux"
    store = manifest.setdefault("entries", {})

    ok = skipped = failed = 0

    for row in entries:
        entry_id = str(row["id"])
        prompt = str(row["prompt"])
        out = IMAGES_DIR / f"{entry_id}.png"

        if skip_existing and find_image_rel(entry_id):
            skipped += 1
            print(f"[skip] {entry_id}")
            continue

        print(f"\n=== [Forge] {entry_id} ===")
        try:
            meta = generate_one(forge, prompt, negative=negative, out_path=out, cfg=cfg)
            # Always drop rating after a new image so auto-loop won't redo forever
            _clear_ratings([entry_id])
            store[entry_id] = {
                "id": entry_id,
                "prompt": prompt,
                "title": row.get("title"),
                "image": f"images/{entry_id}.png",
                "status": "ok",
                "source": "forge-flux",
                "model": cfg.get("model"),
                "generated_at": _utc_now(),
                "needs_review": True,
                **meta,
            }
            save_manifest(manifest)
            ok += 1
            print(f"[ok] {entry_id} ({meta['bytes']} bytes, seed={meta.get('seed')})")
            if delay_s > 0:
                time.sleep(delay_s)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, RuntimeError, OSError) as exc:
            failed += 1
            store[entry_id] = {
                "id": entry_id,
                "status": "error",
                "source": "forge-flux",
                "error": str(exc),
                "failed_at": _utc_now(),
            }
            save_manifest(manifest)
            print(f"[fail] {entry_id}: {exc}", file=sys.stderr)
            if not continue_on_error:
                break

    manifest["updated_at"] = _utc_now()
    save_manifest(manifest)
    summary = {"ok": ok, "skipped": skipped, "failed": failed, "total": len(entries)}
    print("\nSummary:", json.dumps(summary, ensure_ascii=False))
    return summary


# Back-compat name used by older docs / start.sh
generate_batch_gpu = generate_batch_forge


def main() -> int:
    parser = argparse.ArgumentParser(description="Forge Flux batch for LoRA curation")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--skip-existing", action="store_true", default=True)
    parser.add_argument("--no-skip-existing", action="store_false", dest="skip_existing")
    parser.add_argument("--continue-on-error", action="store_true", default=True)
    parser.add_argument("--no-continue-on-error", action="store_false", dest="continue_on_error")
    parser.add_argument("--delay", type=float, default=5.0)
    parser.add_argument("--ids", nargs="*", help="Specific curation ids")
    parser.add_argument(
        "--rejected-only",
        action="store_true",
        help="Regenerate entries rated reject (new seed); clears their rating",
    )
    parser.add_argument(
        "--include-maybe",
        action="store_true",
        help="With --rejected-only, also redo 'maybe'",
    )
    args = parser.parse_args()
    generate_batch_forge(
        limit=args.limit,
        skip_existing=args.skip_existing,
        continue_on_error=args.continue_on_error,
        delay_s=args.delay,
        ids=args.ids,
        rejected_only=args.rejected_only,
        include_maybe=args.include_maybe,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
