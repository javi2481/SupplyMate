"""Tests for session scope history push/pop/clear/loads."""

from __future__ import annotations

from app.core.models import AnalyticalScope
from app.services import scope as scope_svc
from app.services.scoping import history as hist


def test_push_then_pop_restores_prior_scope():
    s0 = AnalyticalScope()
    s1 = scope_svc.add(s0, "category", "Cosmética")
    stack = hist.push([], s0)
    assert len(stack) == 1
    restored, remaining = hist.pop(stack)
    assert restored is not None
    assert restored.model_dump() == s0.model_dump()
    assert remaining == []
    # s1 unused — documents the intended navigation pair
    assert s1.categories == ["Cosmética"]


def test_push_idempotent_when_top_equals_scope():
    s = scope_svc.add(AnalyticalScope(), "category", "Cosmética")
    stack = hist.push([], s)
    again = hist.push(stack, s)
    assert len(again) == 1
    assert again[0].model_dump() == s.model_dump()


def test_push_cap_drops_oldest():
    stack: list[AnalyticalScope] = []
    for i in range(hist.HISTORY_CAP):
        stack = hist.push(stack, AnalyticalScope(categories=[f"C{i}"]))
    assert len(stack) == hist.HISTORY_CAP
    stack = hist.push(stack, AnalyticalScope(categories=["NEW"]))
    assert len(stack) == hist.HISTORY_CAP
    assert stack[0].categories == ["C1"]
    assert stack[-1].categories == ["NEW"]


def test_pop_empty_returns_none():
    assert hist.pop([]) is None


def test_clear_returns_empty():
    assert hist.clear() == []


def test_loads_validates_and_drops_invalid():
    raw = [
        {"categories": ["Cosmética"]},
        {"categories": 123},  # invalid
        "not-a-dict",
        {"categories": ["Cabello"], "health_buckets": ["stockout_risk"]},
    ]
    loaded = hist.loads(raw)
    assert len(loaded) == 2
    assert loaded[0].categories == ["Cosmética"]
    assert loaded[1].health_buckets == ["stockout_risk"]


def test_loads_none_and_empty():
    assert hist.loads(None) == []
    assert hist.loads([]) == []


def test_scope_reexports_history_ops():
    assert hasattr(scope_svc, "push_history")
    assert hasattr(scope_svc, "pop_history")
    assert hasattr(scope_svc, "clear_history")
    assert hasattr(scope_svc, "loads_history")
