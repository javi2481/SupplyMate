"""Tests for analytical scope add/remove/reset/cache_key."""

from __future__ import annotations

from app.core.models import AnalyticalScope
from app.services import scope as scope_svc
from app.catalog.store import SALES_AS_OF


def test_add_idempotent():
    base = scope_svc.empty_scope()
    once = scope_svc.add(base, "category", "Cabello")
    twice = scope_svc.add(once, "category", "Cabello")
    assert once.categories == ["Cabello"]
    assert twice.categories == ["Cabello"]
    assert twice is once or twice.model_dump() == once.model_dump()


def test_add_or_two_categories():
    base = scope_svc.empty_scope()
    s1 = scope_svc.add(base, "category", "A")
    s2 = scope_svc.add(s1, "category", "B")
    assert set(s2.categories) == {"A", "B"}


def test_add_respects_limit():
    base = scope_svc.empty_scope()
    current = base
    for i in range(6):
        current = scope_svc.add(current, "category", f"C{i}")
    assert len(current.categories) == 5


def test_remove_and_reset():
    base = scope_svc.add(scope_svc.empty_scope(), "category", "A")
    base = scope_svc.add(base, "coverage_bucket", "0–3 días")
    removed = scope_svc.remove(base, "category", "A")
    assert removed.categories == []
    assert removed.coverage_buckets == ["0–3 días"]
    assert scope_svc.reset().model_dump() == scope_svc.empty_scope().model_dump()


def test_cache_key_order_independent():
    a = AnalyticalScope(categories=["B", "A"])
    b = AnalyticalScope(categories=["A", "B"])
    assert scope_svc.cache_key(a) == scope_svc.cache_key(b)
    assert SALES_AS_OF.isoformat() in scope_svc.cache_key(a)


def test_scope_from_query_params():
    s = scope_svc.scope_from_query_params(
        categories=["X"],
        coverage_buckets=["0–3 días"],
        health_buckets=["stockout_risk"],
        suppliers=["Prov"],
        highlight_product_id="6033436",
    )
    assert s.categories == ["X"]
    assert s.highlight_product_id == "6033436"


def test_add_invalid_dimension_noop():
    base = scope_svc.empty_scope()
    assert scope_svc.add(base, "invalid_dim", "x") is base


def test_remove_missing_value_noop():
    base = scope_svc.add(scope_svc.empty_scope(), "category", "A")
    assert scope_svc.remove(base, "category", "missing") is base


def test_set_and_clear_highlight():
    highlighted = scope_svc.set_highlight(scope_svc.empty_scope(), "6033436")
    assert highlighted.highlight_product_id == "6033436"
    cleared = scope_svc.clear_highlight(highlighted)
    assert cleared.highlight_product_id == ""
    assert scope_svc.clear_highlight(scope_svc.empty_scope()).highlight_product_id == ""
