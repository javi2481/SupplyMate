"""In-memory rate limiter for POST /chat."""

from __future__ import annotations

import time
from collections import defaultdict

_hits: dict[str, list[float]] = defaultdict(list)


def reset_rate_limits() -> None:
    _hits.clear()


def allow_request(client_id: str, limit: int, window_sec: int = 60) -> bool:
    if limit <= 0:
        return True
    now = time.time()
    window_start = now - window_sec
    recent = [t for t in _hits[client_id] if t > window_start]
    if len(recent) >= limit:
        _hits[client_id] = recent
        return False
    recent.append(now)
    _hits[client_id] = recent
    return True
