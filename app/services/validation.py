"""Request validation & clamping."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.config.settings import Settings
from app.models.schemas import GenerateRequest
from app.services import workflow_loader


class ValidationError(ValueError):
    pass


_IMAGE_ID_RE = re.compile(r"^\d{4}/\d{2}/[a-f0-9]{32}\.(webp|png|jpe?g)$", re.I)


def normalize_generate_request(body: GenerateRequest, settings: Settings) -> dict[str, Any]:
    if len(body.prompt) > settings.max_prompt_length:
        raise ValidationError(f"prompt too long (max {settings.max_prompt_length})")
    if len(body.negative_prompt) > settings.max_prompt_length:
        raise ValidationError(f"negative_prompt too long (max {settings.max_prompt_length})")

    workflow = (body.workflow or settings.default_workflow).strip()
    if workflow not in settings.allowed_workflows_list:
        raise ValidationError(
            f"workflow '{workflow}' is not allowed; choose one of: {', '.join(settings.allowed_workflows_list)}"
        )
    try:
        workflow_loader.load_workflow_template(settings, workflow)
    except workflow_loader.WorkflowError as exc:
        raise ValidationError(str(exc)) from exc

    width = int(body.width if body.width is not None else settings.default_width)
    height = int(body.height if body.height is not None else settings.default_height)
    steps = int(body.steps if body.steps is not None else settings.default_steps)
    cfg = float(body.cfg if body.cfg is not None else settings.default_cfg)
    batch = int(body.batch_size or 1)

    if width < 64 or height < 64:
        raise ValidationError("width/height must be >= 64")
    if width > settings.max_width or height > settings.max_height:
        raise ValidationError(f"width/height exceed limits ({settings.max_width}x{settings.max_height})")
    if steps < 1 or steps > settings.max_steps:
        raise ValidationError(f"steps must be between 1 and {settings.max_steps}")
    if batch < 1 or batch > settings.max_batch_size:
        raise ValidationError(f"batch_size must be between 1 and {settings.max_batch_size}")
    if cfg <= 0 or cfg > 30:
        raise ValidationError("cfg must be in (0, 30]")

    model = (body.model or settings.default_model).strip()
    if not model or "/" in model or ".." in model or model.startswith("."):
        raise ValidationError("invalid model name")
    # Check checkpoint exists under MODELS_PATH/checkpoints
    ckpt = Path(settings.models_path) / "checkpoints" / model
    if not ckpt.is_file():
        raise ValidationError(
            f"model '{model}' not found under {settings.models_path}/checkpoints — "
            "place the checkpoint file on the GPU host volume"
        )

    seed = int(body.seed)
    return {
        "prompt": body.prompt,
        "negative_prompt": body.negative_prompt,
        "width": width,
        "height": height,
        "steps": steps,
        "cfg": cfg,
        "seed": seed,
        "model": model,
        "workflow": workflow,
        "batch_size": batch,
        "output_format": settings.default_format,
        "quality": settings.image_quality,
    }


def safe_image_id(image_id: str) -> str:
    value = str(image_id or "").strip().lstrip("/")
    if not _IMAGE_ID_RE.match(value):
        raise ValidationError("invalid image_id")
    # FastAPI path params may encode as YYYY%2FMM%2F... — accept decoded form only
    if ".." in value or value.startswith("/"):
        raise ValidationError("invalid image_id")
    return value
