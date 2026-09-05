"""Unit tests for Explore KPI → scope actions."""

from __future__ import annotations

from app.core.models import AnalyticalScope, InteractionEvent
from app.services.analytics import metrics
from ui.composition import kpi_actions as ka


def test_stockout_kpi_adds_health_bucket():
    scope = AnalyticalScope(categories=["Cosmética"])
    out = ka.apply_kpi_action(scope, ka.KPI_STOCKOUT_RISK)
    assert out is not None
    assert out.categories == ["Cosmética"]
    assert metrics.BUCKET_STOCKOUT_RISK in out.health_buckets


def test_understock_kpi_adds_health_bucket():
    scope = AnalyticalScope(categories=["Cosmética"])
    out = ka.apply_kpi_action(scope, ka.KPI_UNDERSTOCK)
    assert out is not None
    assert metrics.BUCKET_UNDERSTOCK in out.health_buckets


def test_products_strips_extra_filters():
    scope = AnalyticalScope(
        categories=["Cosmética"],
        health_buckets=[metrics.BUCKET_STOCKOUT_RISK],
        coverage_buckets=["0–3 días"],
        highlight_product_id="123",
    )
    out = ka.apply_kpi_action(scope, ka.KPI_PRODUCTS)
    assert out is not None
    assert out.categories == ["Cosmética"]
    assert out.health_buckets == []
    assert out.coverage_buckets == []
    assert out.highlight_product_id == ""


def test_products_noop_when_already_clean():
    scope = AnalyticalScope(categories=["Cosmética"])
    assert ka.apply_kpi_action(scope, ka.KPI_PRODUCTS) is None


def test_coverage_kpi_is_noop():
    scope = AnalyticalScope(categories=["Cosmética"])
    assert ka.apply_kpi_action(scope, ka.KPI_COVERAGE) is None


def test_idempotent_health_add():
    scope = AnalyticalScope(
        categories=["Cosmética"],
        health_buckets=[metrics.BUCKET_STOCKOUT_RISK],
    )
    out = ka.apply_kpi_action(scope, ka.KPI_STOCKOUT_RISK)
    assert out is not None
    assert out.health_buckets == [metrics.BUCKET_STOCKOUT_RISK]


def test_interaction_event_accepts_kpi_and_nav():
    kpi = InteractionEvent(
        source="kpi",
        action="add_filter",
        dimension=ka.KPI_STOCKOUT_RISK,
        label_human=ka.KPI_STOCKOUT_RISK,
    )
    nav = InteractionEvent(source="nav", action="back", label_human="Volver")
    strip = InteractionEvent(
        source="kpi",
        action="strip_filters",
        dimension=ka.KPI_PRODUCTS,
        label_human=ka.KPI_PRODUCTS,
    )
    assert kpi.source == "kpi"
    assert nav.action == "back"
    assert strip.action == "strip_filters"
