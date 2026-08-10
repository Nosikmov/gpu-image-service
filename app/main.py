"""GPU Image Service — FastAPI entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.api.system import router as system_router
from app.config.settings import get_settings
from app.logging_setup import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level)
    logger.info(
        "api_start env=%s workflows=%s models_path=%s",
        settings.app_env,
        ",".join(settings.allowed_workflows_list),
        settings.models_path,
    )
    from pathlib import Path

    ckpt = Path(settings.models_path) / "checkpoints" / settings.default_model
    if not ckpt.is_file():
        logger.error(
            "default_model_missing path=%s — place checkpoint before calling /api/v1/generate",
            ckpt,
        )
    yield
    logger.info("api_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="GPU Image Service",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.enable_docs else None,
        redoc_url=None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(system_router)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
