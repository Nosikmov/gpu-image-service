"""Redis client helper."""

from __future__ import annotations

from functools import lru_cache

import redis

from app.config.settings import Settings, get_settings


@lru_cache
def _client_for(url: str) -> redis.Redis:
    return redis.Redis.from_url(url, decode_responses=True)


def get_redis(settings: Settings | None = None) -> redis.Redis:
    s = settings or get_settings()
    return _client_for(s.redis_url)


def reset_redis_clients() -> None:
    _client_for.cache_clear()
