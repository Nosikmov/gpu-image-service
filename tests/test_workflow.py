"""Workflow template filling (no ComfyUI)."""

from __future__ import annotations

from app.config.settings import get_settings
from app.services import workflow_loader


def test_build_prompt_graph(env_dirs, fake_redis):
    settings = get_settings()
    graph = workflow_loader.build_prompt_graph(
        settings,
        {
            "workflow": "sdxl",
            "prompt": "a goblin",
            "negative_prompt": "blurry",
            "width": 512,
            "height": 768,
            "steps": 12,
            "cfg": 6.5,
            "seed": 42,
            "model": "sd_xl_base_1.0.safetensors",
            "batch_size": 1,
        },
    )
    assert graph["4"]["inputs"]["ckpt_name"] == "sd_xl_base_1.0.safetensors"
    assert graph["6"]["inputs"]["text"] == "a goblin"
    assert graph["5"]["inputs"]["width"] == 512
    assert graph["5"]["inputs"]["height"] == 768
    assert graph["3"]["inputs"]["seed"] == 42
    assert graph["3"]["inputs"]["steps"] == 12
    assert graph["3"]["inputs"]["cfg"] == 6.5
