"""Simple Redis-backed counters for /metrics."""

from __future__ import annotations

from typing import Any

from app.config.settings import Settings
from app.services import queue as queue_service
from app.services.redis_client import get_redis


def incr(settings: Settings, field: str, by: int = 1) -> None:
    get_redis(settings).hincrby(settings.metrics_key, field, by)


def add_duration(settings: Settings, seconds: float) -> None:
    r = get_redis(settings)
    pipe = r.pipeline()
    pipe.hincrbyfloat(settings.metrics_key, "generation_time_sum", float(seconds))
    pipe.hincrby(settings.metrics_key, "generation_time_count", 1)
    pipe.execute()


def snapshot(settings: Settings) -> dict[str, Any]:
    r = get_redis(settings)
    raw = r.hgetall(settings.metrics_key) or {}
    completed = int(raw.get("jobs_completed") or 0)
    failed = int(raw.get("jobs_failed") or 0)
    total = int(raw.get("jobs_total") or (completed + failed))
    sum_t = float(raw.get("generation_time_sum") or 0.0)
    count_t = int(raw.get("generation_time_count") or 0)
    avg = (sum_t / count_t) if count_t else None
    return {
        "queue_size": queue_service.queue_size(settings),
        "jobs_total": total,
        "jobs_completed": completed,
        "jobs_failed": failed,
        "generation_time_avg_sec": avg,
    }
