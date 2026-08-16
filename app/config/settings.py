"""Application settings loaded from environment / .env."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "production"
    log_level: str = "INFO"
    enable_docs: bool = False
    privacy_mode: bool = True

    api_host: str = "0.0.0.0"
    api_port: int = 8080
    api_key: str = Field(default="", min_length=0)

    cors_origins: str = "*"

    redis_url: str = "redis://redis:6379/0"
    job_queue_key: str = "gis:jobs:queue"
    job_key_prefix: str = "gis:job:"
    worker_heartbeat_key: str = "gis:worker:heartbeat"
    worker_heartbeat_ttl_sec: int = 30
    job_ttl_sec: int = 60 * 60 * 24 * 7
    stuck_job_timeout_sec: int = 900
    max_retries: int = 2
    retry_backoff_sec: float = 2.0

    comfyui_url: str = "http://comfyui:8188"
    comfyui_timeout_sec: int = 600
    comfyui_poll_interval_sec: float = 1.0

    models_path: str = "/data/models"
    workflows_path: str = "/app/workflows"
    generated_path: str = "/data/generated"
    save_png: bool = False

    default_width: int = 768
    default_height: int = 768
    default_steps: int = 20
    default_cfg: float = 7.0
    default_format: Literal["webp", "jpeg", "png"] = "webp"
    image_quality: int = 90

    max_width: int = 1536
    max_height: int = 1536
    max_steps: int = 50
    max_batch_size: int = 1
    max_prompt_length: int = 4000

    allowed_workflows: str = "sdxl,sdxl_icon"
    default_workflow: str = "sdxl"
    default_model: str = "sd_xl_base_1.0.safetensors"
    default_lora: str = "rpg_item_icons_sdxl.safetensors"
    default_lora_strength: float = 0.85
    allowed_loras: str = "rpg_item_icons_sdxl.safetensors"

    worker_id: str = "worker-1"
    metrics_key: str = "gis:metrics"

    @property
    def cors_origins_list(self) -> list[str]:
        raw = self.cors_origins.strip()
        if raw == "*":
            return ["*"]
        return [x.strip() for x in raw.split(",") if x.strip()]

    @property
    def allowed_workflows_list(self) -> list[str]:
        return [x.strip() for x in self.allowed_workflows.split(",") if x.strip()]

    @property
    def allowed_loras_list(self) -> list[str]:
        return [x.strip() for x in self.allowed_loras.split(",") if x.strip()]

    @field_validator("api_key")
    @classmethod
    def _strip_key(cls, value: str) -> str:
        return (value or "").strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()
