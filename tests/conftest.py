"""Shared pytest fixtures — no GPU / ComfyUI required."""

from __future__ import annotations

import shutil
from pathlib import Path

import fakeredis
import pytest
from fastapi.testclient import TestClient

from app.config import settings as settings_mod
from app.services import redis_client as redis_mod


REPO = Path(__file__).resolve().parents[1]
WORKFLOW_SRC = REPO / "workflows" / "sdxl.json"
API_KEY = "test-api-key-please-change"


@pytest.fixture()
def env_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    models = tmp_path / "models"
    generated = tmp_path / "generated"
    workflows = tmp_path / "workflows"
    for sub in ("checkpoints", "loras", "vae", "controlnet"):
        (models / sub).mkdir(parents=True)
    generated.mkdir()
    workflows.mkdir()
    shutil.copy(WORKFLOW_SRC, workflows / "sdxl.json")
    # Dummy checkpoint so validation passes without real weights
    (models / "checkpoints" / "sd_xl_base_1.0.safetensors").write_bytes(b"fake-checkpoint")

    monkeypatch.setenv("API_KEY", API_KEY)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/15")
    monkeypatch.setenv("MODELS_PATH", str(models))
    monkeypatch.setenv("GENERATED_PATH", str(generated))
    monkeypatch.setenv("WORKFLOWS_PATH", str(workflows))
    monkeypatch.setenv("COMFYUI_URL", "http://comfyui.test:8188")
    monkeypatch.setenv("ALLOWED_WORKFLOWS", "sdxl")
    monkeypatch.setenv("DEFAULT_MODEL", "sd_xl_base_1.0.safetensors")
    monkeypatch.setenv("PRIVACY_MODE", "true")
    monkeypatch.setenv("ENABLE_DOCS", "false")

    settings_mod.get_settings.cache_clear()
    redis_mod.reset_redis_clients()
    yield {"models": models, "generated": generated, "workflows": workflows}
    settings_mod.get_settings.cache_clear()
    redis_mod.reset_redis_clients()


@pytest.fixture()
def fake_redis(env_dirs, monkeypatch: pytest.MonkeyPatch):
    server = fakeredis.FakeRedis(decode_responses=True)

    def _get(_settings=None):
        return server

    monkeypatch.setattr(redis_mod, "get_redis", _get)
    # Modules that did `from ... import get_redis` keep a local binding.
    import app.services.job_store as job_store
    import app.services.metrics_store as metrics_store
    import app.services.queue as queue_mod

    monkeypatch.setattr(queue_mod, "get_redis", _get)
    monkeypatch.setattr(job_store, "get_redis", _get)
    monkeypatch.setattr(metrics_store, "get_redis", _get)
    return server


@pytest.fixture()
def client(fake_redis) -> TestClient:
    from app.main import create_app

    settings_mod.get_settings.cache_clear()
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {API_KEY}"}
