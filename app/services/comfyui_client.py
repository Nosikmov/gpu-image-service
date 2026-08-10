"""Thin ComfyUI HTTP client (no generation logic in API process)."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

import httpx

from app.config.settings import Settings

logger = logging.getLogger(__name__)


class ComfyUIError(RuntimeError):
    pass


def ping(settings: Settings) -> bool:
    url = f"{settings.comfyui_url.rstrip('/')}/system_stats"
    with httpx.Client(timeout=5.0) as client:
        resp = client.get(url)
        return resp.status_code == 200


def queue_prompt(settings: Settings, prompt_graph: dict[str, Any], client_id: str | None = None) -> str:
    cid = client_id or uuid.uuid4().hex
    url = f"{settings.comfyui_url.rstrip('/')}/prompt"
    payload = {"prompt": prompt_graph, "client_id": cid}
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, json=payload)
        if resp.status_code >= 400:
            raise ComfyUIError(f"ComfyUI /prompt HTTP {resp.status_code}: {resp.text[:400]}")
        data = resp.json()
    prompt_id = data.get("prompt_id")
    if not prompt_id:
        raise ComfyUIError(f"ComfyUI response missing prompt_id: {data!r}")
    return str(prompt_id)


def wait_for_history(
    settings: Settings,
    prompt_id: str,
    *,
    timeout_sec: float | None = None,
) -> dict[str, Any]:
    timeout = float(timeout_sec if timeout_sec is not None else settings.comfyui_timeout_sec)
    deadline = time.time() + timeout
    url = f"{settings.comfyui_url.rstrip('/')}/history/{prompt_id}"
    with httpx.Client(timeout=30.0) as client:
        while time.time() < deadline:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if prompt_id in data:
                    return data[prompt_id]
            time.sleep(settings.comfyui_poll_interval_sec)
    raise ComfyUIError(f"ComfyUI timed out waiting for prompt_id={prompt_id}")


def download_image(settings: Settings, filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
    url = f"{settings.comfyui_url.rstrip('/')}/view"
    params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    with httpx.Client(timeout=120.0) as client:
        resp = client.get(url, params=params)
        if resp.status_code >= 400:
            raise ComfyUIError(f"ComfyUI /view HTTP {resp.status_code}")
        return resp.content


def first_output_image_ref(history_entry: dict[str, Any]) -> tuple[str, str, str]:
    """Return (filename, subfolder, type) for the first saved image in history."""
    outputs = history_entry.get("outputs") or {}
    for _node_id, node_out in outputs.items():
        images = node_out.get("images") if isinstance(node_out, dict) else None
        if not images:
            continue
        img = images[0]
        filename = img.get("filename")
        if not filename:
            continue
        return (
            str(filename),
            str(img.get("subfolder") or ""),
            str(img.get("type") or "output"),
        )
    raise ComfyUIError("ComfyUI history has no output images")
