import threading
import time

TTL = 300  # seconds

_store: dict = {}
_lock = threading.Lock()


def get(key: str):
    with _lock:
        entry = _store.get(key)
        if entry is None:
            return None
        if time.time() - entry["timestamp"] > TTL:
            del _store[key]
            return None
        return entry["data"]


def set(key: str, value) -> None:
    with _lock:
        _store[key] = {"data": value, "timestamp": time.time()}


def is_valid(key: str) -> bool:
    with _lock:
        entry = _store.get(key)
        if entry is None:
            return False
        if time.time() - entry["timestamp"] > TTL:
            del _store[key]
            return False
        return True
