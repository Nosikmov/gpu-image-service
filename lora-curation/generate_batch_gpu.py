#!/usr/bin/env python3
"""Generate curation images via GPU Comfy relay (DreamShaper XL, free local GPU)."""

from __future__ import annotations

import argparse
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

from paths import IMAGES_DIR, find_image_rel, load_prompts, load_manifest, save_manifest  # noqa: E402
from style import MONSTER_NEGATIVE  # noqa: E402

DEFAULT_RELAY = "http://89.111.168.5:8191"
DEFAULT_CKPT = "DreamShaperXL_alpha2.safetensors"
CHUNK_SIZE = 400


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _relay_url() -> str:
    return (os.environ.get("COMFY_RELAY_URL") or DEFAULT_RELAY).rstrip("/")


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


def _http_bytes(url: str, timeout: float = 120) -> bytes:
    req = urllib.request.Request(url, headers={"Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _upload_long_prompt(relay: str, prompt: str, negative: str) -> str:
    init = _http_json("POST", f"{relay}/api/v1/chunks/init", {})
    session_id = str(init["session_id"])
    for field, text in (("prompt", prompt), ("negative", negative)):
        for i in range(0, len(text), CHUNK_SIZE):
            _http_json(
                "POST",
                f"{relay}/api/v1/chunks/append",
                {"session_id": session_id, "field": field, "chunk": text[i : i + CHUNK_SIZE]},
            )
    gen = _http_json(
        "POST",
        f"{relay}/api/v1/chunks/generate",
        {
            "session_id": session_id,
            "width": 768,
            "height": 768,
            "steps": 22,
            "cfg": 6.5,
            "model": DEFAULT_CKPT,
        },
    )
    return str(gen["job_id"])


def _wait_job(relay: str, job_id: str, *, poll_s: float = 2.0, timeout_s: float = 300) -> dict[str, Any]:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        job = _http_json("GET", f"{relay}/api/v1/jobs/{job_id}")
        status = str(job.get("status") or "")
        if status in ("done", "completed", "success"):
            return job
        if status in ("failed", "error"):
            raise RuntimeError(job.get("error") or job.get("message") or "job failed")
        time.sleep(poll_s)
    raise TimeoutError(f"job {job_id} timed out after {timeout_s}s")


def generate_one(
    relay: str,
    entry_id: str,
    prompt: str,
    *,
    negative: str,
    out_path: Path,
) -> dict[str, Any]:
    job_id = _upload_long_prompt(relay, prompt, negative)
    job = _wait_job(relay, job_id)
    image_url = str(job.get("image_url") or "")
    if not image_url:
        raise RuntimeError(f"no image_url in job {job_id}")
    if image_url.startswith("/"):
        image_url = relay + image_url
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(_http_bytes(image_url))
    return {"job_id": job_id, "image_url": image_url, "bytes": out_path.stat().st_size}


def generate_batch_gpu(
    *,
    limit: int | None,
    skip_existing: bool,
    continue_on_error: bool,
    delay_s: float,
    ids: list[str] | None,
) -> dict[str, int]:
    relay = _relay_url()
    _http_json("GET", f"{relay}/health")

    pack = load_prompts()
    entries = pack["entries"]
    if ids:
        id_set = set(ids)
        entries = [e for e in entries if e["id"] in id_set]
    if limit is not None:
        entries = entries[:limit]

    manifest = load_manifest()
    manifest.setdefault("version", 1)
    manifest.setdefault("generator", "comfy-gpu")
    store = manifest.setdefault("entries", {})

    negative = MONSTER_NEGATIVE
    ok = skipped = failed = 0

    for row in entries:
        entry_id = str(row["id"])
        prompt = str(row["prompt"])
        out = IMAGES_DIR / f"{entry_id}.png"

        if skip_existing and find_image_rel(entry_id):
            skipped += 1
            print(f"[skip] {entry_id}")
            continue

        print(f"\n=== [GPU] {entry_id} ===")
        try:
            meta = generate_one(relay, entry_id, prompt, negative=negative, out_path=out)
            store[entry_id] = {
                "id": entry_id,
                "prompt": prompt,
                "image": f"images/{entry_id}.png",
                "status": "ok",
                "source": "comfy-gpu",
                "model": DEFAULT_CKPT,
                "generated_at": _utc_now(),
                **meta,
            }
            save_manifest(manifest)
            ok += 1
            print(f"[ok] {entry_id} ({meta['bytes']} bytes)")
            if delay_s > 0:
                time.sleep(delay_s)
        except (urllib.error.URLError, TimeoutError, RuntimeError, OSError) as exc:
            failed += 1
            store[entry_id] = {
                "id": entry_id,
                "status": "error",
                "source": "comfy-gpu",
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


def main() -> int:
    parser = argparse.ArgumentParser(description="GPU Comfy batch for LoRA curation")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--skip-existing", action="store_true", default=True)
    parser.add_argument("--no-skip-existing", action="store_false", dest="skip_existing")
    parser.add_argument("--continue-on-error", action="store_true", default=True)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--ids", nargs="*", help="Specific curation ids")
    args = parser.parse_args()
    generate_batch_gpu(
        limit=args.limit,
        skip_existing=args.skip_existing,
        continue_on_error=args.continue_on_error,
        delay_s=args.delay,
        ids=args.ids,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
