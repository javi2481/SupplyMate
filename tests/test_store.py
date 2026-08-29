import pytest

from app.replenishment import calculate_replenishment
from app.services import catalog_service
from app.store import get_store
from tests.catalog_ids import SKU_HIGH_QTY, SKU_SAMPLE, SKU_ZERO_QTY


def test_store_loads_all_resources():
    store = get_store()
    assert len(store.products) > 10000
    master = store.get_master(SKU_SAMPLE)
    assert master.product_name
    assert master.price is not None


def test_store_master_has_reorder_fields():
    master = get_store().get_master(SKU_HIGH_QTY)
    assert master.reorder_point is not None
    assert master.min_stock is not None


def test_store_search_by_name():
    hits = get_store().search("47 street", limit=5)
    assert hits
    assert any(h.product_id == SKU_ZERO_QTY for h in hits)


def test_catalog_service_recommendation_matches_formula():
    rec = catalog_service.get_replenishment_recommendation(SKU_HIGH_QTY)
    master = catalog_service.get_master(SKU_HIGH_QTY)
    expected = calculate_replenishment(
        product_id=master.product_id,
        current_stock=master.current_stock,
        total_units_sold_last_30=master.units_sold_30d,
        lead_time_days=master.lead_time_days,
        safety_stock=master.safety_stock,
    )
    assert rec.recommended_quantity == expected.recommended_quantity
    assert rec.recommended_quantity == 172


def test_zero_qty_sku():
    rec = catalog_service.get_replenishment_recommendation(SKU_ZERO_QTY)
    assert rec.recommended_quantity == 0
