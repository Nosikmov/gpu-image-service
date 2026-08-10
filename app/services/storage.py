"""Persist generated images under /data/generated/YYYY/MM/."""

from __future__ import annotations

import io
import logging
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from app.config.settings import Settings

logger = logging.getLogger(__name__)


def ensure_storage_dirs(settings: Settings) -> None:
    Path(settings.generated_path).mkdir(parents=True, exist_ok=True)
    for sub in ("checkpoints", "loras", "vae", "controlnet"):
        (Path(settings.models_path) / sub).mkdir(parents=True, exist_ok=True)


def save_image_bytes(
    settings: Settings,
    job_id: str,
    raw_png_or_bytes: bytes,
    *,
    now: datetime | None = None,
) -> str:
    """Save image; return relative image_id like 2026/08/<job_id>.webp."""
    ts = now or datetime.now(timezone.utc)
    rel_dir = f"{ts:%Y}/{ts:%m}"
    out_dir = Path(settings.generated_path) / rel_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    image = Image.open(io.BytesIO(raw_png_or_bytes))
    image.load()
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA" if "A" in image.getbands() else "RGB")

    fmt = settings.default_format.lower()
    if fmt == "jpg":
        fmt = "jpeg"
    ext = "jpg" if fmt == "jpeg" else fmt
    filename = f"{job_id}.{ext}"
    dest = out_dir / filename

    save_kwargs: dict = {}
    if fmt in {"webp", "jpeg"}:
        save_kwargs["quality"] = int(settings.image_quality)
    if fmt == "webp":
        save_kwargs["method"] = 4
    if fmt == "jpeg" and image.mode == "RGBA":
        image = image.convert("RGB")

    image.save(dest, format=fmt.upper() if fmt != "jpg" else "JPEG", **save_kwargs)

    if settings.save_png:
        png_path = out_dir / f"{job_id}.png"
        if image.mode == "RGBA" or fmt == "png":
            image.save(png_path, format="PNG")
        else:
            Image.open(io.BytesIO(raw_png_or_bytes)).convert("RGBA").save(png_path, format="PNG")

    image_id = f"{rel_dir}/{filename}"
    logger.info("image_saved job_id=%s image_id=%s bytes=%s", job_id, image_id, dest.stat().st_size)
    return image_id
