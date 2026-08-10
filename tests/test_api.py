"""API and queue tests (no GPU)."""

from __future__ import annotations

from unittest.mock import patch

from app.config.settings import get_settings
from app.services import queue as queue_service


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ready_not_ready_without_deps(client):
    with (
        patch("app.services.comfyui_client.ping", return_value=False),
        patch("app.services.queue.worker_is_alive", return_value=False),
    ):
        r = client.get("/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "not_ready"
    assert body["redis"] is True
    assert body["comfyui"] is False
    assert body["worker"] is False


def test_ready_ok(client, fake_redis):
    settings = get_settings()
    queue_service.beat_worker(settings, "worker-test")
    with patch("app.services.comfyui_client.ping", return_value=True):
        r = client.get("/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ready"
    assert body["redis"] and body["comfyui"] and body["worker"]


def test_generate_requires_auth(client):
    r = client.post("/api/v1/generate", json={"prompt": "a cat", "workflow": "sdxl"})
    assert r.status_code == 401


def test_generate_rejects_bad_key(client):
    r = client.post(
        "/api/v1/generate",
        json={"prompt": "a cat", "workflow": "sdxl"},
        headers={"Authorization": "Bearer wrong"},
    )
    assert r.status_code == 401


def test_generate_and_job(client, auth_headers, fake_redis):
    r = client.post(
        "/api/v1/generate",
        json={
            "prompt": "medieval fantasy goblin warrior",
            "workflow": "sdxl",
            "width": 768,
            "height": 768,
            "steps": 20,
        },
        headers=auth_headers,
    )
    assert r.status_code == 202
    data = r.json()
    assert data["status"] == "queued"
    job_id = data["job_id"]
    assert len(job_id) == 32

    settings = get_settings()
    assert queue_service.queue_size(settings) == 1
    queued = fake_redis.lrange(settings.job_queue_key, 0, -1)
    assert queued == [job_id]

    jr = client.get(f"/api/v1/jobs/{job_id}", headers=auth_headers)
    assert jr.status_code == 200
    job = jr.json()
    assert job["job_id"] == job_id
    assert job["status"] == "queued"
    assert job["progress"] == 0
    assert job["image_url"] is None
    assert job["error"] is None


def test_validation_max_width(client, auth_headers):
    r = client.post(
        "/api/v1/generate",
        json={"prompt": "x", "workflow": "sdxl", "width": 99999, "height": 768},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_validation_forbidden_workflow(client, auth_headers):
    r = client.post(
        "/api/v1/generate",
        json={"prompt": "x", "workflow": "not-a-real-workflow"},
        headers=auth_headers,
    )
    assert r.status_code == 422
    assert "not allowed" in r.json()["detail"].lower() or "not allowed" in str(r.json()).lower()


def test_validation_missing_model(client, auth_headers, env_dirs):
    r = client.post(
        "/api/v1/generate",
        json={"prompt": "x", "workflow": "sdxl", "model": "does_not_exist.safetensors"},
        headers=auth_headers,
    )
    assert r.status_code == 422
    assert "not found" in r.json()["detail"].lower()


def test_validation_path_traversal_model(client, auth_headers):
    r = client.post(
        "/api/v1/generate",
        json={"prompt": "x", "workflow": "sdxl", "model": "../evil.safetensors"},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_job_not_found(client, auth_headers):
    r = client.get("/api/v1/jobs/" + ("a" * 32), headers=auth_headers)
    assert r.status_code == 404


def test_metrics(client, auth_headers, fake_redis):
    r = client.get("/metrics")
    assert r.status_code == 200
    body = r.json()
    assert "queue_size" in body
    assert "jobs_total" in body
    assert "worker_status" in body
