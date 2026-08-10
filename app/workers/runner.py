"""Worker loop: dequeue jobs, call ComfyUI, store images."""

from __future__ import annotations

import logging
import signal
import time
from pathlib import Path

from app.config.settings import get_settings
from app.logging_setup import setup_logging
from app.models.schemas import JobStatus
from app.services import comfyui_client, job_store, metrics_store, queue, storage, workflow_loader

logger = logging.getLogger(__name__)
_STOP = False


def _handle_signal(signum, _frame) -> None:  # noqa: ANN001
    global _STOP
    logger.info("worker_signal signum=%s", signum)
    _STOP = True


def process_job(settings, job_id: str) -> None:
    job = job_store.get_job(settings, job_id)
    if not job:
        logger.warning("job_missing job_id=%s", job_id)
        return

    attempts = int(job.get("attempts") or 0) + 1
    started = time.time()
    job_store.update_job(
        settings,
        job_id,
        status=JobStatus.processing.value,
        progress=5,
        started_at=started,
        attempts=attempts,
        error=None,
    )
    metrics_store.incr(settings, "jobs_total", 1)
    params = job.get("params") or {}
    workflow = params.get("workflow") or job.get("workflow")

    logger.info(
        "job_start job_id=%s workflow=%s attempt=%s",
        job_id,
        workflow,
        attempts,
    )

    try:
        storage.ensure_storage_dirs(settings)
        graph = workflow_loader.build_prompt_graph(settings, params)
        job_store.update_job(settings, job_id, progress=20)
        prompt_id = comfyui_client.queue_prompt(settings, graph)
        job_store.update_job(settings, job_id, progress=40)
        history = comfyui_client.wait_for_history(settings, prompt_id)
        job_store.update_job(settings, job_id, progress=80)
        filename, subfolder, folder_type = comfyui_client.first_output_image_ref(history)
        raw = comfyui_client.download_image(settings, filename, subfolder, folder_type)
        image_id = storage.save_image_bytes(settings, job_id, raw)
        finished = time.time()
        duration = finished - started
        job_store.update_job(
            settings,
            job_id,
            status=JobStatus.completed.value,
            progress=100,
            image_id=image_id,
            finished_at=finished,
            error=None,
        )
        metrics_store.incr(settings, "jobs_completed", 1)
        metrics_store.add_duration(settings, duration)
        logger.info(
            "job_done job_id=%s workflow=%s status=completed duration=%.2f image_id=%s",
            job_id,
            workflow,
            duration,
            image_id,
        )
    except Exception as exc:  # noqa: BLE001
        finished = time.time()
        duration = finished - started
        err = f"{type(exc).__name__}: {exc}"
        transient = isinstance(exc, (comfyui_client.ComfyUIError, TimeoutError, ConnectionError, OSError))
        can_retry = transient and attempts <= settings.max_retries
        if can_retry:
            logger.warning(
                "job_retry job_id=%s attempt=%s err=%s",
                job_id,
                attempts,
                type(exc).__name__,
            )
            job_store.update_job(
                settings,
                job_id,
                status=JobStatus.queued.value,
                progress=0,
                error=err,
                finished_at=None,
            )
            time.sleep(settings.retry_backoff_sec * attempts)
            queue.enqueue_job(settings, job_id)
            return

        job_store.update_job(
            settings,
            job_id,
            status=JobStatus.failed.value,
            progress=100,
            error=err[:1000],
            finished_at=finished,
        )
        metrics_store.incr(settings, "jobs_failed", 1)
        logger.error(
            "job_done job_id=%s workflow=%s status=failed duration=%.2f err=%s",
            job_id,
            workflow,
            duration,
            type(exc).__name__,
        )


def reclaim_stuck_jobs(settings) -> None:
    """Best-effort: mark processing jobs older than timeout as failed.

    Without a secondary index we scan recent keys by pattern (bounded).
    """
    from app.services.redis_client import get_redis

    r = get_redis(settings)
    now = time.time()
    cursor = 0
    pattern = f"{settings.job_key_prefix}*"
    while True:
        cursor, keys = r.scan(cursor=cursor, match=pattern, count=100)
        for key in keys:
            raw = r.hgetall(key)
            if not raw or raw.get("status") != JobStatus.processing.value:
                continue
            try:
                started = float(raw.get("started_at") or 0)
            except ValueError:
                started = 0
            if started and (now - started) > settings.stuck_job_timeout_sec:
                job_id = raw.get("job_id") or key.rsplit(":", 1)[-1]
                job_store.update_job(
                    settings,
                    job_id,
                    status=JobStatus.failed.value,
                    error="stuck_job_timeout",
                    finished_at=now,
                    progress=100,
                )
                metrics_store.incr(settings, "jobs_failed", 1)
                logger.error("job_stuck job_id=%s", job_id)
        if cursor == 0:
            break


def run_forever() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)
    storage.ensure_storage_dirs(settings)
    ckpt = Path(settings.models_path) / "checkpoints" / settings.default_model
    if not ckpt.is_file():
        logger.error(
            "default_model_missing path=%s — generations will fail until the checkpoint is placed",
            ckpt,
        )
    logger.info("worker_start id=%s redis=%s comfy=%s", settings.worker_id, settings.redis_url, settings.comfyui_url)

    last_reclaim = 0.0
    while not _STOP:
        queue.beat_worker(settings, settings.worker_id)
        now = time.time()
        if now - last_reclaim > 60:
            try:
                reclaim_stuck_jobs(settings)
            except Exception as exc:  # noqa: BLE001
                logger.warning("reclaim_failed err=%s", type(exc).__name__)
            last_reclaim = now

        job_id = queue.dequeue_job(settings, timeout_sec=3)
        if not job_id:
            continue
        process_job(settings, job_id)

    logger.info("worker_stop id=%s", settings.worker_id)


if __name__ == "__main__":
    run_forever()
