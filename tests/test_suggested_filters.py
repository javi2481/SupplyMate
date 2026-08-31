"""Tests for deterministic suggested filter chips."""

from __future__ import annotations

from app.models import (
    AnalyticalScope,
    CategoryBar,
    CoverageBar,
    InventoryDashboard,
    PurchaseListItem,
)
from app.services import metrics, suggested_filters


def _snap(**kwargs) -> InventoryDashboard:
    base = InventoryDashboard(
        skus=100,
        stockout_risk=10,
        by_category=[CategoryBar(category="Cabello", recommended_quantity=50, sku_count=5)],
        coverage=[CoverageBar(bucket="0–3 días", sku_count=8)],
    )
    return base.model_copy(update=kwargs)


def test_suggest_at_most_three():
    items = [
        PurchaseListItem(
            product_id="1",
            product_name="Prod A",
            supplier="ProvX",
            recommended_quantity=20,
        )
    ]
    chips = suggested_filters.suggest_next_filters(_snap(), items, AnalyticalScope())
    assert len(chips) <= 3
    assert all(chip.action for chip in chips)


def test_suggest_skips_active_category():
    scope = AnalyticalScope(categories=["Cabello"])
    chips = suggested_filters.suggest_next_filters(_snap(), [], scope)
    assert not any(
        chip.action == suggested_filters.ACTION_FILTER_CATEGORY
        and chip.args.get("category") == "Cabello"
        for chip in chips
    )


def test_suggest_stockout_health():
    scope = AnalyticalScope()
    chips = suggested_filters.suggest_next_filters(_snap(stockout_risk=5), [], scope)
    health = [
        c
        for c in chips
        if c.action == suggested_filters.ACTION_FILTER_HEALTH
    ]
    assert health
    assert health[0].args["health_bucket"] == metrics.BUCKET_STOCKOUT_RISK


def test_suggest_open_sku_from_top_item():
    items = [
        PurchaseListItem(
            product_id="99",
            product_name="Top SKU",
            supplier="ProvX",
            recommended_quantity=100,
        )
    ]
    snap = InventoryDashboard(skus=1, stockout_risk=0, by_category=[], coverage=[])
    chips = suggested_filters.suggest_next_filters(snap, items, AnalyticalScope())
    open_chips = [c for c in chips if c.action == suggested_filters.ACTION_OPEN_SKU]
    assert open_chips
    assert open_chips[0].args["product_id"] == "99"
