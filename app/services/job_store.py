"""Job persistence in Redis hashes."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

from app.config.settings import Settings
from app.models.schemas import JobStatus
from app.services.redis_client import get_redis


def _key(settings: Settings, job_id: str) -> str:
    return f"{settings.job_key_prefix}{job_id}"


def create_job(settings: Settings, params: dict[str, Any]) -> dict[str, Any]:
    job_id = uuid.uuid4().hex
    now = time.time()
    job = {
        "job_id": job_id,
        "status": JobStatus.queued.value,
        "progress": 0,
        "error": None,
        "image_id": None,
        "workflow": params["workflow"],
        "model": params["model"],
        "params_json": json.dumps(params, ensure_ascii=False),
        "created_at": now,
        "started_at": None,
        "finished_at": None,
        "attempts": 0,
        "updated_at": now,
    }
    r = get_redis(settings)
    pipe = r.pipeline()
    pipe.hset(_key(settings, job_id), mapping=_serialize(job))
    pipe.expire(_key(settings, job_id), settings.job_ttl_sec)
    pipe.execute()
    return job


def get_job(settings: Settings, job_id: str) -> dict[str, Any] | None:
    raw = get_redis(settings).hgetall(_key(settings, job_id))
    if not raw:
        return None
    return _deserialize(raw)


def update_job(settings: Settings, job_id: str, **fields: Any) -> dict[str, Any] | None:
    key = _key(settings, job_id)
    r = get_redis(settings)
    if not r.exists(key):
        return None
    fields = {**fields, "updated_at": time.time()}
    r.hset(key, mapping=_serialize(fields))
    r.expire(key, settings.job_ttl_sec)
    return get_job(settings, job_id)


def _serialize(data: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in data.items():
        if v is None:
            out[k] = ""
        elif isinstance(v, (dict, list)):
            out[k] = json.dumps(v, ensure_ascii=False)
        else:
            out[k] = str(v)
    return out


def _deserialize(raw: dict[str, str]) -> dict[str, Any]:
    job: dict[str, Any] = dict(raw)
    for num_key in ("progress", "attempts"):
        if num_key in job and job[num_key] != "":
            job[num_key] = int(float(job[num_key]))
    for ts_key in ("created_at", "started_at", "finished_at", "updated_at"):
        if ts_key in job and job[ts_key] != "":
            job[ts_key] = float(job[ts_key])
        elif ts_key in job:
            job[ts_key] = None
    for nullable in ("error", "image_id"):
        if job.get(nullable) == "":
            job[nullable] = None
    if job.get("params_json"):
        try:
            job["params"] = json.loads(job["params_json"])
        except json.JSONDecodeError:
            job["params"] = {}
    return job
