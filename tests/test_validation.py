"""Unit tests for validation helpers."""

from __future__ import annotations

import pytest

from app.config.settings import get_settings
from app.services import validation


def test_safe_image_id_ok(env_dirs, fake_redis):
    get_settings.cache_clear()
    assert validation.safe_image_id("2026/08/" + ("a" * 32) + ".webp").endswith(".webp")


def test_safe_image_id_rejects(env_dirs, fake_redis):
    with pytest.raises(validation.ValidationError):
        validation.safe_image_id("../etc/passwd")
    with pytest.raises(validation.ValidationError):
        validation.safe_image_id("2026/08/not-hex.webp")
