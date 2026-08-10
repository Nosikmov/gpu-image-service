"""System endpoints: health, ready, metrics."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from app.config.settings import get_settings
from app.models.schemas import HealthResponse, MetricsResponse, ReadyResponse
from app.services import comfyui_client, metrics_store, queue as queue_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadyResponse)
def ready() -> ReadyResponse:
    settings = get_settings()
    redis_ok = False
    comfy_ok = False
    worker_ok = False
    detail: dict = {}
    try:
        redis_ok = queue_service.ping_redis(settings)
    except Exception as exc:  # noqa: BLE001
        detail["redis_error"] = type(exc).__name__
        logger.warning("ready_redis_failed err=%s", type(exc).__name__)
    try:
        comfy_ok = comfyui_client.ping(settings)
    except Exception as exc:  # noqa: BLE001
        detail["comfyui_error"] = type(exc).__name__
        logger.warning("ready_comfy_failed err=%s", type(exc).__name__)
    try:
        worker_ok = queue_service.worker_is_alive(settings)
    except Exception as exc:  # noqa: BLE001
        detail["worker_error"] = type(exc).__name__

    status = "ready" if (redis_ok and comfy_ok and worker_ok) else "not_ready"
    return ReadyResponse(
        status=status,
        redis=redis_ok,
        comfyui=comfy_ok,
        worker=worker_ok,
        detail=detail,
    )


@router.get("/metrics", response_model=MetricsResponse)
def metrics() -> MetricsResponse:
    settings = get_settings()
    snap = metrics_store.snapshot(settings)
    worker_alive = queue_service.worker_is_alive(settings)
    return MetricsResponse(
        queue_size=snap["queue_size"],
        jobs_total=snap["jobs_total"],
        jobs_completed=snap["jobs_completed"],
        jobs_failed=snap["jobs_failed"],
        generation_time_avg_sec=snap["generation_time_avg_sec"],
        worker_status="alive" if worker_alive else "down",
    )
