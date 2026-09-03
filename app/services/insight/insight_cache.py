"""In-memory TTL cache for analyze responses."""

from __future__ import annotations

import time
from typing import Any

from app.core.models import AnalyzeResponse

_TTL_SECONDS = 300.0
_store: dict[str, tuple[float, AnalyzeResponse]] = {}


def cache_key(mode: str, scope_key: str, events_hash: str) -> str:
    return f"{mode}|{scope_key}|{events_hash}"


def events_hash(events: list) -> str:
    import hashlib
    import json

    raw = json.dumps([e.model_dump() if hasattr(e, "model_dump") else e for e in events])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def get(key: str) -> AnalyzeResponse | None:
    entry = _store.get(key)
    if entry is None:
        return None
    expires, value = entry
    if time.monotonic() > expires:
        _store.pop(key, None)
        return None
    return value


def set(key: str, value: AnalyzeResponse) -> None:
    _store[key] = (time.monotonic() + _TTL_SECONDS, value)


def reset() -> None:
    _store.clear()
