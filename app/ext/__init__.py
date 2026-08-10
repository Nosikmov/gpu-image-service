"""Optional extension points (stubs). Implement later without rewriting core paths."""

from __future__ import annotations

from typing import Any, Protocol


class ObjectStorage(Protocol):
    """Future S3/MinIO backend for generated images."""

    def put(self, key: str, data: bytes, content_type: str) -> str: ...

    def url_for(self, key: str) -> str: ...


class JobNotifier(Protocol):
    """Future webhook / callback when a job completes or fails."""

    def notify(self, job: dict[str, Any]) -> None: ...


# Reserved Redis key namespaces for future multi-queue / priorities:
#   gis:jobs:queue:high | gis:jobs:queue:normal | gis:jobs:queue:low
# Reserved job fields: priority, cancel_requested, webhook_url, gpu_id
