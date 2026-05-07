from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any


UTC = timezone.utc


@dataclass
class CacheEntry:
    value: Any
    stored_at: datetime


class SimpleTTLCache:
    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl = timedelta(seconds=ttl_seconds)
        self._store: dict[str, CacheEntry] = {}
        self._lock = Lock()

    def set(self, key: str, value: Any) -> Any:
        with self._lock:
            self._store[key] = CacheEntry(value=value, stored_at=datetime.now(UTC))
        return value

    def get(self, key: str, allow_stale: bool = False) -> Any | None:
        with self._lock:
            entry = self._store.get(key)

        if entry is None:
            return None

        if allow_stale or datetime.now(UTC) - entry.stored_at <= self.ttl:
            return entry.value

        return None

    def size(self) -> int:
        with self._lock:
            return len(self._store)
