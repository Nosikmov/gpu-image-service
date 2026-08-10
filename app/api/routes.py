"""v1 generate / jobs / images routes."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.api.deps import require_api_key
from app.config.settings import Settings, get_settings
from app.models.schemas import GenerateRequest, GenerateResponse, JobResponse, JobStatus
from app.services import job_store, queue as queue_service, validation

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(require_api_key)], tags=["v1"])


@router.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_202_ACCEPTED)
def generate(body: GenerateRequest, settings: Settings = Depends(get_settings)) -> GenerateResponse:
    try:
        params = validation.normalize_generate_request(body, settings)
    except validation.ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    job = job_store.create_job(settings, params)
    queue_service.enqueue_job(settings, job["job_id"])
    if settings.privacy_mode:
        logger.info(
            "job_enqueued job_id=%s workflow=%s width=%s height=%s steps=%s",
            job["job_id"],
            params["workflow"],
            params["width"],
            params["height"],
            params["steps"],
        )
    else:
        logger.info(
            "job_enqueued job_id=%s workflow=%s prompt_len=%s",
            job["job_id"],
            params["workflow"],
            len(params["prompt"]),
        )
    return GenerateResponse(job_id=job["job_id"], status=JobStatus.queued)


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str, settings: Settings = Depends(get_settings)) -> JobResponse:
    job = job_store.get_job(settings, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    image_url = None
    if job.get("status") == JobStatus.completed.value and job.get("image_id"):
        image_url = f"/api/v1/images/{job['image_id']}"
    duration = None
    if job.get("started_at") and job.get("finished_at"):
        duration = float(job["finished_at"]) - float(job["started_at"])
    return JobResponse(
        job_id=job["job_id"],
        status=JobStatus(job["status"]),
        progress=int(job.get("progress") or 0),
        image_url=image_url,
        error=job.get("error"),
        workflow=job.get("workflow"),
        created_at=job.get("created_at"),
        started_at=job.get("started_at"),
        finished_at=job.get("finished_at"),
        duration_sec=duration,
    )


@router.get("/images/{image_id:path}")
def get_image(image_id: str, settings: Settings = Depends(get_settings)):
    try:
        safe = validation.safe_image_id(image_id)
    except validation.ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    path = Path(settings.generated_path) / safe
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    media = "image/webp"
    if path.suffix.lower() == ".png":
        media = "image/png"
    elif path.suffix.lower() in {".jpg", ".jpeg"}:
        media = "image/jpeg"
    return FileResponse(path, media_type=media, filename=path.name)
