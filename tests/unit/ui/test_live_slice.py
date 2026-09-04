"""Scope key change must invalidate cached Explore slice_data."""

from __future__ import annotations

from app.core.models import AnalyticalScope
from app.services import scope as scope_svc
from ui.composition.live_slice import scope_cache_key, select_live_slice


def test_select_live_slice_reuses_cache_when_key_matches():
    cached = {"dashboard": {"skus": 10}}
    calls = {"n": 0}

    def fetch() -> dict:
        calls["n"] += 1
        return {"dashboard": {"skus": 99}}

    result, key = select_live_slice(
        scope_key="k1",
        cached_key="k1",
        cached_slice=cached,
        fetch=fetch,
    )
    assert result is cached
    assert key == "k1"
    assert calls["n"] == 0


def test_select_live_slice_refetches_when_key_differs():
    cached = {"dashboard": {"skus": 10}}
    fresh = {"dashboard": {"skus": 3, "by_category": []}}
    calls = {"n": 0}

    def fetch() -> dict:
        calls["n"] += 1
        return fresh

    result, key = select_live_slice(
        scope_key="k2",
        cached_key="k1",
        cached_slice=cached,
        fetch=fetch,
    )
    assert result is fresh
    assert key == "k2"
    assert calls["n"] == 1


def test_select_live_slice_refetches_when_cache_missing():
    fresh = {"dashboard": {"skus": 5}}

    result, key = select_live_slice(
        scope_key="k1",
        cached_key=None,
        cached_slice=None,
        fetch=lambda: fresh,
    )
    assert result is fresh
    assert key == "k1"


def test_select_live_slice_keeps_cache_if_fetch_fails_on_same_key():
    cached = {"dashboard": {"skus": 10}}

    result, key = select_live_slice(
        scope_key="k1",
        cached_key="k1",
        cached_slice=cached,
        fetch=lambda: None,
    )
    assert result is cached
    assert key == "k1"


def test_select_live_slice_returns_fresh_none_but_preserves_stale_only_on_match():
    """When the key changed and fetch fails, still return previous slice as fallback."""
    cached = {"dashboard": {"skus": 10}}

    result, key = select_live_slice(
        scope_key="k2",
        cached_key="k1",
        cached_slice=cached,
        fetch=lambda: None,
    )
    assert result is cached
    assert key == "k2"


def test_scope_cache_key_changes_when_category_added():
    empty = AnalyticalScope()
    narrowed = scope_svc.add(empty, "category", "Cuidado del Cabello")
    assert scope_cache_key(empty) != scope_cache_key(narrowed)
