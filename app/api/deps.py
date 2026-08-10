"""Auth dependency: Bearer API key."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config.settings import Settings, get_settings

_bearer = HTTPBearer(auto_error=False)


def require_api_key(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
    settings: Settings = Depends(get_settings),
) -> None:
    expected = settings.api_key
    if not expected:
        # Misconfigured service — refuse rather than open anonymously.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API_KEY is not configured on the server",
        )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    provided = (credentials.credentials or "").strip()
    if provided != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
