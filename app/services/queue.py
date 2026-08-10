"""Redis queue + worker heartbeat."""

from __future__ import annotations

import time

from app.config.settings import Settings
from app.services.redis_client import get_redis


def ping_redis(settings: Settings) -> bool:
    return bool(get_redis(settings).ping())


def enqueue_job(settings: Settings, job_id: str) -> None:
    get_redis(settings).rpush(settings.job_queue_key, job_id)


def dequeue_job(settings: Settings, timeout_sec: int = 5) -> str | None:
    item = get_redis(settings).blpop(settings.job_queue_key, timeout=timeout_sec)
    if not item:
        return None
    _key, job_id = item
    return str(job_id)


def queue_size(settings: Settings) -> int:
    return int(get_redis(settings).llen(settings.job_queue_key) or 0)


def beat_worker(settings: Settings, worker_id: str) -> None:
    r = get_redis(settings)
    r.hset(
        settings.worker_heartbeat_key,
        mapping={"worker_id": worker_id, "ts": str(time.time())},
    )
    r.expire(settings.worker_heartbeat_key, settings.worker_heartbeat_ttl_sec)


def worker_is_alive(settings: Settings) -> bool:
    raw = get_redis(settings).hgetall(settings.worker_heartbeat_key)
    if not raw or "ts" not in raw:
        return False
    try:
        ts = float(raw["ts"])
    except (TypeError, ValueError):
        return False
    return (time.time() - ts) <= settings.worker_heartbeat_ttl_sec
