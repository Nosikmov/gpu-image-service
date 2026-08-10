"""Load and fill ComfyUI workflow JSON templates."""

from __future__ import annotations

import copy
import json
import random
from pathlib import Path
from typing import Any

from app.config.settings import Settings


class WorkflowError(RuntimeError):
    pass


def workflow_path(settings: Settings, name: str) -> Path:
    return Path(settings.workflows_path) / f"{name}.json"


def load_workflow_template(settings: Settings, name: str) -> dict[str, Any]:
    path = workflow_path(settings, name)
    if not path.is_file():
        raise WorkflowError(f"workflow file missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise WorkflowError("workflow JSON must be an object of node_id -> node")
    return data


def build_prompt_graph(settings: Settings, params: dict[str, Any]) -> dict[str, Any]:
    """Return ComfyUI API-format prompt graph with placeholders filled."""
    graph = copy.deepcopy(load_workflow_template(settings, params["workflow"]))
    seed = int(params.get("seed", -1))
    if seed < 0:
        seed = random.randint(0, 2**32 - 1)

    replacements = {
        "{{PROMPT}}": params["prompt"],
        "{{NEGATIVE_PROMPT}}": params.get("negative_prompt") or "",
        "{{WIDTH}}": str(int(params["width"])),
        "{{HEIGHT}}": str(int(params["height"])),
        "{{STEPS}}": str(int(params["steps"])),
        "{{CFG}}": str(float(params["cfg"])),
        "{{SEED}}": str(seed),
        "{{MODEL}}": params["model"],
        "{{BATCH_SIZE}}": str(int(params.get("batch_size") or 1)),
    }

    def fill(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: fill(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [fill(v) for v in obj]
        if isinstance(obj, str):
            out = obj
            for token, value in replacements.items():
                out = out.replace(token, value)
            # coerce numeric strings when original placeholder was alone
            if obj in {"{{WIDTH}}", "{{HEIGHT}}", "{{STEPS}}", "{{SEED}}", "{{BATCH_SIZE}}"}:
                return int(out)
            if obj == "{{CFG}}":
                return float(out)
            return out
        return obj

    return fill(graph)
