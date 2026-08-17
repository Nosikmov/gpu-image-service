#!/usr/bin/env python3
"""Local web UI to rate LoRA curation images (approve / reject / maybe)."""

from __future__ import annotations

import argparse
import json
import mimetypes
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import (  # noqa: E402
    IMAGES_DIR,
    find_image_rel,
    load_manifest,
    load_prompts,
    load_ratings,
    save_ratings,
)

REVIEW_HTML = _ROOT / "reviewer.html"
VALID_RATINGS = {"approve", "reject", "maybe", "unset"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _stats(ratings: dict[str, Any]) -> dict[str, int]:
    entries = ratings.get("entries") or {}
    counts = {"approve": 0, "reject": 0, "maybe": 0, "unset": 0}
    for row in entries.values():
        key = str(row.get("rating") or "unset")
        if key not in counts:
            key = "unset"
        counts[key] += 1
    return counts


def _merged_items() -> list[dict[str, Any]]:
    pack = load_prompts()
    manifest = load_manifest()
    ratings = load_ratings()
    manifest_entries = manifest.get("entries") or {}
    rating_entries = ratings.get("entries") or {}

    items: list[dict[str, Any]] = []
    for row in pack["entries"]:
        entry_id = str(row["id"])
        image_rel = None
        image_exists = False
        mrow = manifest_entries.get(entry_id) or {}
        if mrow.get("image"):
            image_rel = str(mrow["image"])
            image_exists = (_ROOT / image_rel).is_file()
        if not image_exists:
            image_rel = find_image_rel(entry_id)
            image_exists = image_rel is not None
        rrow = rating_entries.get(entry_id) or {}
        items.append(
            {
                "id": entry_id,
                "prompt": row.get("prompt"),
                "category": row.get("category"),
                "monster_id": row.get("monster_id"),
                "variant": row.get("variant"),
                "image": image_rel,
                "image_exists": image_exists,
                "rating": rrow.get("rating") or "unset",
                "note": rrow.get("note") or "",
                "rated_at": rrow.get("rated_at"),
            }
        )
    return items


class ReviewHandler(BaseHTTPRequestHandler):
    server_version = "LoRAReview/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[review] {self.address_string()} - {fmt % args}")

    def _send_json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> Any:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/reviewer.html"):
            if not REVIEW_HTML.is_file():
                self._send_json({"error": "reviewer.html missing"}, status=500)
                return
            body = REVIEW_HTML.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/api/items":
            qs = parse_qs(parsed.query)
            rating_filter = (qs.get("rating") or [None])[0]
            only_with_image = (qs.get("only_with_image") or ["0"])[0] == "1"
            items = _merged_items()
            if only_with_image:
                items = [i for i in items if i["image_exists"]]
            if rating_filter in VALID_RATINGS:
                items = [i for i in items if i["rating"] == rating_filter]
            ratings = load_ratings()
            self._send_json(
                {
                    "count": len(items),
                    "stats": _stats(ratings),
                    "trigger_word": load_prompts().get("trigger_word_suggestion"),
                    "items": items,
                }
            )
            return

        if path == "/api/stats":
            ratings = load_ratings()
            self._send_json({"stats": _stats(ratings), "total_prompts": load_prompts().get("count")})
            return

        if path.startswith("/images/"):
            rel = path.lstrip("/")
            file_path = _ROOT / rel
            if not file_path.is_file() or _ROOT not in file_path.resolve().parents:
                self.send_error(404)
                return
            mime, _ = mimetypes.guess_type(str(file_path))
            body = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime or "application/octet-stream")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/api/rate":
            self.send_error(404)
            return

        payload = self._read_json()
        entry_id = str(payload.get("id") or "").strip()
        rating = str(payload.get("rating") or "unset").strip()
        note = str(payload.get("note") or "").strip()

        if not entry_id:
            self._send_json({"error": "id required"}, status=400)
            return
        if rating not in VALID_RATINGS:
            self._send_json({"error": f"rating must be one of {sorted(VALID_RATINGS)}"}, status=400)
            return

        pack_ids = {str(r["id"]) for r in load_prompts()["entries"]}
        if entry_id not in pack_ids:
            self._send_json({"error": "unknown id"}, status=404)
            return

        ratings = load_ratings()
        ratings.setdefault("version", 1)
        ratings.setdefault("entries", {})
        if rating == "unset":
            ratings["entries"].pop(entry_id, None)
        else:
            ratings["entries"][entry_id] = {
                "id": entry_id,
                "rating": rating,
                "note": note,
                "rated_at": _utc_now(),
            }
        ratings["updated_at"] = _utc_now()
        save_ratings(ratings)
        self._send_json({"ok": True, "id": entry_id, "rating": rating, "stats": _stats(ratings)})


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve LoRA curation review UI")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    httpd = ThreadingHTTPServer((args.host, args.port), ReviewHandler)
    url = f"http://{args.host}:{args.port}/"
    print(f"LoRA review UI: {url}")
    print("Keys: A approve | R reject | M maybe | ←/→ navigate | N note")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
