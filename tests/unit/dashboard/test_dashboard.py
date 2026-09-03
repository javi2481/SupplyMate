"""Inventory dashboard aggregates for the chat (no Superset)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.models import AnalyticalScope, PurchaseListItem
from app.services import dashboard


def _row(**kwargs) -> dict:
    item = {
        "product_id": "1",
        "product_name": "A",
        "barcode": "",
        "supplier": "X",
        "category": "Cosmetica",
        "subcategory": "",
        "current_stock": 10,
        "reorder_point": 5,
        "below_reorder_point": False,
        "average_daily_demand": 1.0,
        "days_of_supply": 10.0,
        "health_bucket": "healthy",
        "recommended_quantity": 0,
        "units_sold_30d": 0,
    }
    item.update(kwargs)
    return item


def test_purchase_list_item_requires_product_id():
    with pytest.raises(ValidationError):
        PurchaseListItem(product_name="x", recommended_quantity=1)
    with pytest.raises(ValidationError):
        PurchaseListItem(product_id="", product_name="x", recommended_quantity=1)


def test_purchase_items_skips_rows_without_product_id():
    rows = [
        _row(product_id="", recommended_quantity=10, product_name="Ghost"),
        _row(product_id="ok-1", recommended_quantity=5, product_name="Real"),
    ]
    items = dashboard.purchase_items(rows, limit=25)
    assert len(items) == 1
    assert items[0].product_id == "ok-1"


def test_coverage_bucket_edges():
    assert dashboard.coverage_bucket(None) is None
    assert dashboard.coverage_bucket(0) == "0–3 días"
    assert dashboard.coverage_bucket(2.9) == "0–3 días"
    assert dashboard.coverage_bucket(3) == "3–7 días"
    assert dashboard.coverage_bucket(7) == "7–14 días"
    assert dashboard.coverage_bucket(14) == "14–30 días"
    assert dashboard.coverage_bucket(30) == "30+ días"


def test_from_rows_health_and_charts():
    rows = [
        _row(
            product_id="s",
            health_bucket="stockout_risk",
            days_of_supply=1.0,
            recommended_quantity=20,
            category="Cabello",
            units_sold_30d=100,
        ),
        _row(
            product_id="u",
            health_bucket="understock",
            days_of_supply=5.0,
            recommended_quantity=5,
            category="Cabello",
            units_sold_30d=40,
        ),
        _row(
            product_id="o",
            health_bucket="overstock",
            days_of_supply=40.0,
            recommended_quantity=0,
            category="Fragancias",
            units_sold_30d=200,
        ),
        _row(
            product_id="h",
            health_bucket="healthy",
            days_of_supply=12.0,
            recommended_quantity=0,
            category="Fragancias",
        ),
        _row(
            product_id="n",
            health_bucket="healthy",
            days_of_supply=None,
            recommended_quantity=0,
            category="",
        ),
    ]
    snap = dashboard.from_rows(rows)
    assert snap.skus == 5
    assert snap.stockout_risk == 1
    assert snap.understock == 1
    assert snap.overstock == 1
    assert snap.healthy == 2
    assert snap.avg_coverage == 14.5
    assert [c.category for c in snap.by_category] == ["Cabello"]
    assert snap.by_category[0].recommended_quantity == 25
    assert snap.by_category[0].sku_count == 2
    assert [c.category for c in snap.by_sales][0] == "Fragancias"
    assert snap.by_sales[0].units_sold == 200
    buckets = {b.bucket: b.sku_count for b in snap.coverage}
    assert buckets["0–3 días"] == 1
    assert buckets["3–7 días"] == 1
    assert buckets["7–14 días"] == 1
    assert buckets["30+ días"] == 1
    assert sum(buckets.values()) == 4


def test_purchase_items_top_limit():
    rows = [
        _row(product_id="a", product_name="A", recommended_quantity=10),
        _row(product_id="b", product_name="B", recommended_quantity=40),
        _row(product_id="c", product_name="C", recommended_quantity=0),
    ]
    items = dashboard.purchase_items(rows, limit=1)
    assert len(items) == 1
    assert items[0].product_id == "b"
    assert items[0].recommended_quantity == 40


def test_purchase_items_critical_before_higher_qty():
    rows = [
        _row(
            product_id="cheap",
            product_name="Cheap",
            recommended_quantity=99,
            operational_priority="normal",
            days_of_supply=20.0,
        ),
        _row(
            product_id="urgent",
            product_name="Urgent",
            recommended_quantity=3,
            operational_priority="critical",
            health_bucket="stockout_risk",
            days_of_supply=0.5,
        ),
    ]
    items = dashboard.purchase_items(rows, limit=2)
    assert items[0].product_id == "urgent"


def test_from_rows_sums_purchase_value():
    rows = [
        _row(recommended_quantity=10, estimated_purchase_value=100.0),
        _row(recommended_quantity=2, estimated_purchase_value=20.0),
        _row(recommended_quantity=5, estimated_purchase_value=None),
    ]
    snap = dashboard.from_rows(rows)
    assert snap.estimated_purchase_value == 120.0



def test_from_rows_empty():
    snap = dashboard.from_rows([])
    assert snap.skus == 0
    assert snap.avg_coverage is None
    assert snap.by_category == []
    assert all(b.sku_count == 0 for b in snap.coverage)


def test_total_recommended_qty():
    assert dashboard.total_recommended_qty([{"recommended_quantity": 10}, {"recommended_quantity": 7}]) == 17
    assert dashboard.total_recommended_qty([]) == 0


def test_filter_rows_single_category():
    rows = [
        _row(product_id="a", category="Cabello"),
        _row(product_id="b", category="Fragancias"),
    ]
    scope = AnalyticalScope(categories=["Cabello"])
    out = dashboard.filter_rows(rows, scope)
    assert len(out) == 1
    assert out[0]["product_id"] == "a"


def test_filter_rows_or_two_categories():
    rows = [
        _row(product_id="a", category="Cabello"),
        _row(product_id="b", category="Fragancias"),
        _row(product_id="c", category="Otros"),
    ]
    scope = AnalyticalScope(categories=["Cabello", "Fragancias"])
    out = dashboard.filter_rows(rows, scope)
    assert {row["product_id"] for row in out} == {"a", "b"}


def test_filter_rows_and_category_plus_coverage():
    rows = [
        _row(product_id="a", category="Cabello", days_of_supply=1.0),
        _row(product_id="b", category="Cabello", days_of_supply=10.0),
        _row(product_id="c", category="Fragancias", days_of_supply=1.0),
    ]
    scope = AnalyticalScope(categories=["Cabello"], coverage_buckets=["0–3 días"])
    out = dashboard.filter_rows(rows, scope)
    assert len(out) == 1
    assert out[0]["product_id"] == "a"


def test_filter_rows_highlight_does_not_filter():
    rows = [
        _row(product_id="a", category="Cabello"),
        _row(product_id="b", category="Fragancias"),
    ]
    scope = AnalyticalScope(highlight_product_id="b")
    out = dashboard.filter_rows(rows, scope)
    assert len(out) == 2


def test_filter_rows_name_token_whole_word():
    rows = [
        _row(product_id="a", product_name="PAMPERS BABYDRY XXG X 8", category="Pañales"),
        _row(product_id="b", product_name="HUGGIES CLASSIC XXXG X 28", category="Pañales"),
        _row(product_id="c", product_name="JABON LIQUIDO", category="Jabon de Tocador"),
    ]
    scope = AnalyticalScope(categories=["Pañales"], name_tokens=["xxg"])
    out = dashboard.filter_rows(rows, scope)
    assert [row["product_id"] for row in out] == ["a"]

