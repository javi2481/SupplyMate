"""Tests for deterministic suggested filter chips."""

from __future__ import annotations

from app.core.models import (
    AnalyticalScope,
    CategoryBar,
    CoverageBar,
    InventoryDashboard,
    PurchaseListItem,
)
from app.services import metrics, suggested_filters


def _item(**kwargs) -> PurchaseListItem:
    base = dict(
        product_id="1",
        product_name="Prod A",
        supplier="ProvX",
        recommended_quantity=20,
    )
    base.update(kwargs)
    return PurchaseListItem(**base)


def _snap(**kwargs) -> InventoryDashboard:
    base = InventoryDashboard(
        skus=100,
        stockout_risk=10,
        by_category=[CategoryBar(category="Cabello", recommended_quantity=50, sku_count=5)],
        coverage=[CoverageBar(bucket="0–3 días", sku_count=8)],
    )
    return base.model_copy(update=kwargs)


def _full_board() -> tuple[InventoryDashboard, list[PurchaseListItem]]:
    snap = InventoryDashboard(
        skus=200,
        stockout_risk=12,
        overstock=4,
        recommended_units=500,
        by_category=[
            CategoryBar(category="A", recommended_quantity=90, sku_count=9),
            CategoryBar(category="B", recommended_quantity=40, sku_count=4),
        ],
        coverage=[CoverageBar(bucket="0–3 días", sku_count=8)],
    )
    items = [
        _item(product_id="99", product_name="Top SKU", supplier="ProvX", recommended_quantity=100),
    ]
    return snap, items


def test_suggest_at_most_six():
    chips = suggested_filters.suggest_next_filters(*_full_board(), AnalyticalScope())
    assert len(chips) <= 6
    assert all(chip.action for chip in chips)


def test_sparse_does_not_pad():
    snap = InventoryDashboard(
        skus=10,
        stockout_risk=0,
        overstock=0,
        recommended_units=0,
        by_category=[CategoryBar(category="Cabello", recommended_quantity=50, sku_count=5)],
        coverage=[CoverageBar(bucket="0–3 días", sku_count=8)],
    )
    chips = suggested_filters.suggest_next_filters(snap, [], AnalyticalScope())
    assert len(chips) == 2
    assert [c.action for c in chips] == [
        suggested_filters.ACTION_FILTER_CATEGORY,
        suggested_filters.ACTION_FILTER_COVERAGE,
    ]


def test_overflow_keeps_first_six_spec_slots():
    chips = suggested_filters.suggest_next_filters(*_full_board(), AnalyticalScope())
    assert len(chips) == 6
    assert [c.action for c in chips] == [
        suggested_filters.ACTION_FILTER_CATEGORY,
        suggested_filters.ACTION_FILTER_CATEGORY,
        suggested_filters.ACTION_FILTER_COVERAGE,
        suggested_filters.ACTION_FILTER_HEALTH,
        suggested_filters.ACTION_FILTER_HEALTH,
        suggested_filters.ACTION_FILTER_SUPPLIER,
    ]
    assert chips[0].args["category"] == "A"
    assert chips[1].args["category"] == "B"
    assert chips[3].args["health_bucket"] == metrics.BUCKET_STOCKOUT_RISK
    assert chips[4].args["health_bucket"] == metrics.BUCKET_OVERSTOCK
    assert chips[5].args["supplier"] == "ProvX"
    assert not any(c.action == suggested_filters.ACTION_OPEN_SKU for c in chips)
    assert not any(c.action == suggested_filters.ACTION_DRAFT_OC for c in chips)


def test_suggest_skips_active_category():
    scope = AnalyticalScope(categories=["Cabello"])
    chips = suggested_filters.suggest_next_filters(_snap(), [], scope)
    assert not any(
        chip.action == suggested_filters.ACTION_FILTER_CATEGORY
        and chip.args.get("category") == "Cabello"
        for chip in chips
    )


def test_skip_active_still_considers_open_sku_and_draft_oc():
    snap, items = _full_board()
    scope = AnalyticalScope(
        categories=["A", "B"],
        coverage_buckets=["0–3 días"],
        health_buckets=[metrics.BUCKET_STOCKOUT_RISK, metrics.BUCKET_OVERSTOCK],
        suppliers=["ProvX"],
    )
    chips = suggested_filters.suggest_next_filters(snap, items, scope)
    actions = [c.action for c in chips]
    assert suggested_filters.ACTION_OPEN_SKU in actions
    assert suggested_filters.ACTION_DRAFT_OC in actions
    assert not any(c.action.startswith("filter_") for c in chips)


def test_cap_board_matches_spec_order():
    chips = suggested_filters.suggest_next_filters(*_full_board(), AnalyticalScope())
    assert [c.args.get("category") or c.args.get("coverage_bucket") or c.args.get("health_bucket") or c.args.get("supplier") for c in chips] == [
        "A",
        "B",
        "0–3 días",
        "stockout_risk",
        "overstock",
        "ProvX",
    ]


def test_draft_oc_only_when_no_other_slots():
    snap = InventoryDashboard(skus=3, recommended_units=40, by_category=[], coverage=[])
    chips = suggested_filters.suggest_next_filters(snap, [], AnalyticalScope())
    assert len(chips) == 1
    assert chips[0].action == suggested_filters.ACTION_DRAFT_OC
    assert chips[0].args == {}


def test_category_label_is_question():
    snap = InventoryDashboard(
        skus=1,
        stockout_risk=0,
        by_category=[CategoryBar(category="Cuidado", recommended_quantity=10, sku_count=2)],
        coverage=[],
    )
    chips = suggested_filters.suggest_next_filters(snap, [], AnalyticalScope())
    cat = next(c for c in chips if c.action == suggested_filters.ACTION_FILTER_CATEGORY)
    assert cat.label == "¿Qué hay en Cuidado?"
    assert "Ver " not in cat.label
    assert "SKUs" not in cat.label


def test_overstock_payload():
    snap = InventoryDashboard(skus=8, overstock=3, stockout_risk=0, by_category=[], coverage=[])
    chips = suggested_filters.suggest_next_filters(snap, [], AnalyticalScope())
    health = [c for c in chips if c.action == suggested_filters.ACTION_FILTER_HEALTH]
    assert health
    assert health[0].args["health_bucket"] == metrics.BUCKET_OVERSTOCK
    assert health[0].label == "¿Hay sobrestock?"


def test_suggest_stockout_health():
    scope = AnalyticalScope()
    chips = suggested_filters.suggest_next_filters(_snap(stockout_risk=5), [], scope)
    health = [c for c in chips if c.action == suggested_filters.ACTION_FILTER_HEALTH]
    assert health
    assert health[0].args["health_bucket"] == metrics.BUCKET_STOCKOUT_RISK


def test_suggest_open_sku_from_top_item():
    items = [
        _item(product_id="99", product_name="Top SKU", supplier="ProvX", recommended_quantity=100),
    ]
    snap = InventoryDashboard(skus=1, stockout_risk=0, by_category=[], coverage=[])
    chips = suggested_filters.suggest_next_filters(snap, items, AnalyticalScope())
    open_chips = [c for c in chips if c.action == suggested_filters.ACTION_OPEN_SKU]
    assert open_chips
    assert open_chips[0].args["product_id"] == "99"
    assert open_chips[0].label.startswith("¿Cuánto pedir de ")
