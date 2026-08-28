#!/usr/bin/env python3
"""Autonomous curation loop: missing images + rejected redo + prompt-file watch.

Run via START_CURATION.bat (starts Forge if needed, then this).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
import webbrowser
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from generate_batch_gpu import (  # noqa: E402
    _forge_alive,
    _wait_forge,
    generate_batch_forge,
)
from parse_prompts_txt import write_prompt_pack_from_txt  # noqa: E402
from paths import (  # noqa: E402
    IMAGES_DIR,
    PROMPTS_PATH,
    find_image_rel,
    load_prompts,
    load_ratings,
)
from serve_reviewer import ReviewHandler  # noqa: E402
from style import TRIGGER_WORD  # noqa: E402

PROMPTS_TXT = _ROOT / "promts-for-generate.txt"
STATUS_PATH = _ROOT / "auto_status.json"
DEFAULT_FORGE = os.environ.get("FORGE_URL", "http://127.0.0.1:7860").rstrip("/")
POLL_S = float(os.environ.get("CURATION_POLL_S", "3"))


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_status(state: str, message: str = "", **extra: Any) -> None:
    payload = {
        "state": state,
        "message": message,
        "updated_at": _utc_now(),
        **extra,
    }
    STATUS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        print(f"[status] {state}: {message}", flush=True)
    except OSError:
        pass


def rebuild_prompts(*, variants: int = 1) -> int:
    if not PROMPTS_TXT.is_file():
        raise FileNotFoundError(PROMPTS_TXT)
    pack = write_prompt_pack_from_txt(
        PROMPTS_TXT,
        PROMPTS_PATH,
        variants=variants,
        trigger=TRIGGER_WORD,
    )
    return len(pack)


def missing_ids() -> list[str]:
    pack = load_prompts()
    out: list[str] = []
    for row in pack["entries"]:
        eid = str(row["id"])
        if not find_image_rel(eid):
            out.append(eid)
    return out


def reject_count() -> int:
    ratings = load_ratings()
    n = 0
    for row in (ratings.get("entries") or {}).values():
        if str(row.get("rating") or "") == "reject":
            n += 1
    return n


def start_reviewer(host: str, port: int) -> ThreadingHTTPServer:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    httpd = ThreadingHTTPServer((host, port), ReviewHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True, name="reviewer")
    t.start()
    return httpd


def curation_tick(*, forge: str, delay_s: float) -> str:
    """One work unit. Returns what was done: idle|rebuilt|generated|regenerated|waiting_forge."""
    # 1) prompts.txt changed -> rebuild
    txt_mtime = PROMPTS_TXT.stat().st_mtime if PROMPTS_TXT.is_file() else 0.0
    json_mtime = PROMPTS_PATH.stat().st_mtime if PROMPTS_PATH.is_file() else 0.0
    if txt_mtime > json_mtime + 0.5 or not PROMPTS_PATH.is_file():
        write_status("rebuilding", "Rebuild prompts.json from promts-for-generate.txt")
        n = rebuild_prompts(variants=1)
        write_status("idle", f"prompts.json updated ({n})")
        return "rebuilt"

    # Need Forge for gen work
    n_rej = reject_count()
    miss = missing_ids()
    if (n_rej > 0 or miss) and not _forge_alive(forge):
        write_status("waiting_forge", "Waiting for Forge API on :7860")
        return "waiting_forge"

    # 2) rejected -> regenerate
    if n_rej > 0:
        write_status("regenerating", f"Regenerating {n_rej} reject(s)", pending=n_rej)
        generate_batch_forge(
            limit=None,
            skip_existing=False,
            continue_on_error=True,
            delay_s=delay_s,
            ids=None,
            rejected_only=True,
            include_maybe=False,
        )
        write_status("idle", "Rejects regenerated - rate new images")
        return "regenerated"

    # 3) missing images -> generate
    if miss:
        write_status("generating", f"Generating {len(miss)} missing", pending=len(miss), ids=miss[:12])
        generate_batch_forge(
            limit=None,
            skip_existing=True,
            continue_on_error=True,
            delay_s=delay_s,
            ids=miss,
            rejected_only=False,
            include_maybe=False,
        )
        write_status("idle", "New images ready - rate in UI")
        return "generated"

    write_status("idle", "Waiting: Reject in UI or new lines in promts-for-generate.txt")
    return "idle"


def run_loop(*, host: str, port: int, forge: str, delay_s: float, open_browser: bool) -> int:
    write_status("starting", "Auto-loop starting")
    if not PROMPTS_PATH.is_file() and PROMPTS_TXT.is_file():
        rebuild_prompts(variants=1)

    httpd = start_reviewer(host, port)
    url = f"http://127.0.0.1:{port}/"
    try:
        print(f"Review UI: {url}")
        print("Auto-loop: missing -> generate | reject -> redo | txt edits -> rebuild")
        print("Ctrl+C to stop")
    except OSError:
        pass
    write_status("idle", f"UI {url}")

    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        while True:
            try:
                action = curation_tick(forge=forge, delay_s=delay_s)
                time.sleep(POLL_S if action in ("idle", "waiting_forge") else 1.0)
            except SystemExit as exc:
                write_status("error", str(exc))
                time.sleep(10)
            except OSError as exc:
                # Windows console flush / socket quirks (Errno 22)
                write_status("error", f"OSError: {exc}")
                time.sleep(5)
            except Exception as exc:  # noqa: BLE001
                write_status("error", str(exc))
                try:
                    print(f"[loop error] {exc}", flush=True)
                except OSError:
                    pass
                time.sleep(5)
    except KeyboardInterrupt:
        try:
            print("\nStopped.")
        except OSError:
            pass
        write_status("stopped", "Stopped")
    finally:
        httpd.shutdown()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Autonomous LoRA curation loop")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--forge", default=DEFAULT_FORGE)
    parser.add_argument("--delay", type=float, default=5.0)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    return run_loop(
        host=args.host,
        port=args.port,
        forge=args.forge.rstrip("/"),
        delay_s=args.delay,
        open_browser=not args.no_browser,
    )


if __name__ == "__main__":
    raise SystemExit(main())
