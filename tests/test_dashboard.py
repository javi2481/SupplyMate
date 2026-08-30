"""Inventory dashboard aggregates for the chat (no Superset)."""

from __future__ import annotations

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


def test_from_rows_empty():
    snap = dashboard.from_rows([])
    assert snap.skus == 0
    assert snap.avg_coverage is None
    assert snap.by_category == []
    assert all(b.sku_count == 0 for b in snap.coverage)


def test_total_recommended_qty():
    assert dashboard.total_recommended_qty([{"recommended_quantity": 10}, {"recommended_quantity": 7}]) == 17
    assert dashboard.total_recommended_qty([]) == 0
