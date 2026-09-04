"""When the analytical scope changes, Explore must refetch the slice."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def select_live_slice(
    *,
    scope_key: str,
    cached_key: str | None,
    cached_slice: dict | None,
    fetch: Callable[[], dict | None],
) -> tuple[dict | None, str]:
    """Return the slice for ``scope_key``, refetching when the key changes.

    Chips, chart clicks, and reset all mutate scope. Reusing a stale
    ``slice_data`` leaves KPIs and the other chart lying about the recorte.
    """
    if cached_slice is not None and cached_key == scope_key:
        return cached_slice, scope_key
    fresh = fetch()
    if fresh is None:
        # Keep last known evidence if the API is down; still advance the key
        # so the next successful fetch is tied to the current scope.
        return cached_slice, scope_key
    return fresh, scope_key


def scope_cache_key(scope: Any) -> str:
    from app.services import scope as scope_svc

    return scope_svc.cache_key(scope)
