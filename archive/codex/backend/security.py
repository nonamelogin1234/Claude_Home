from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from config import Settings


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _get_settings() -> Settings:
    return Settings()


def verify_api_key(
    key: str | None = Depends(api_key_header),
    settings: Settings = Depends(_get_settings),
) -> None:
    if not settings.api_key:
        return

    if key is None or not secrets.compare_digest(key, settings.api_key):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
