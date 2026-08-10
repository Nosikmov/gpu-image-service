"""Pydantic schemas for API and job state."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class JobStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    negative_prompt: str = ""
    width: int | None = None
    height: int | None = None
    steps: int | None = None
    cfg: float | None = None
    seed: int = -1
    model: str | None = None
    workflow: str | None = None
    batch_size: int = 1

    @field_validator("prompt", "negative_prompt", mode="before")
    @classmethod
    def _strip_text(cls, value: Any) -> str:
        return str(value or "").strip()


class GenerateResponse(BaseModel):
    job_id: str
    status: JobStatus = JobStatus.queued


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: int = 0
    image_url: str | None = None
    error: str | None = None
    workflow: str | None = None
    created_at: float | None = None
    started_at: float | None = None
    finished_at: float | None = None
    duration_sec: float | None = None


class HealthResponse(BaseModel):
    status: str = "ok"


class ReadyResponse(BaseModel):
    status: str
    redis: bool
    comfyui: bool
    worker: bool
    detail: dict[str, Any] = Field(default_factory=dict)


class MetricsResponse(BaseModel):
    queue_size: int
    jobs_total: int
    jobs_completed: int
    jobs_failed: int
    generation_time_avg_sec: float | None = None
    worker_status: str
