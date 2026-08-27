"""Shared paths for LoRA curation tooling (self-contained in gpu-image-service)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
IMAGES_DIR = ROOT / "images"
RATINGS_PATH = ROOT / "ratings.json"
MANIFEST_PATH = ROOT / "manifest.json"
PROMPTS_PATH = ROOT / "prompts.json"
EXPORT_DIR = ROOT / "export" / "approved"

_IMAGE_EXTS = (".png", ".webp", ".jpg", ".jpeg")


def game_repo() -> Path:
    """gameFarmling checkout (for promote / rembg into game assets)."""
    env = os.environ.get("GAME_REPO")
    if env:
        return Path(env).expanduser().resolve()
    gpu_root = ROOT.parent
    nested = gpu_root.parent
    if (nested / "frontend" / "public" / "assets").is_dir():
        return nested
    sibling = gpu_root.parent / "gameFarmling"
    if (sibling / "frontend" / "public" / "assets").is_dir():
        return sibling
    raise SystemExit("Set GAME_REPO to the gameFarmling repo root")


def monsters_dir() -> Path:
    return game_repo() / "frontend" / "public" / "assets" / "monsters"


def find_image_rel(entry_id: str) -> str | None:
    """Return relative path images/{id}.ext if file exists on disk."""
    for ext in _IMAGE_EXTS:
        rel = f"images/{entry_id}{ext}"
        if (ROOT / rel).is_file():
            return rel
    return None


def load_prompts() -> dict[str, Any]:
    if not PROMPTS_PATH.is_file():
        raise FileNotFoundError(f"Missing {PROMPTS_PATH}; run build_prompts.py first")
    return json.loads(PROMPTS_PATH.read_text(encoding="utf-8"))


def load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.is_file():
        return {"version": 1, "entries": {}}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def save_manifest(data: dict[str, Any]) -> None:
    MANIFEST_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_ratings() -> dict[str, Any]:
    if not RATINGS_PATH.is_file():
        return {"version": 1, "entries": {}}
    return json.loads(RATINGS_PATH.read_text(encoding="utf-8"))


def save_ratings(data: dict[str, Any]) -> None:
    RATINGS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
