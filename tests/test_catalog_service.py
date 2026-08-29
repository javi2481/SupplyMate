import pytest

from app.models import ProductNotFoundError
from app.replenishment import calculate_replenishment
from app.services import catalog_service
from tests.catalog_ids import SKU_HIGH_QTY, SKU_UNKNOWN, SKU_ZERO_QTY


def test_get_master():
    master = catalog_service.get_master(SKU_HIGH_QTY)
    assert master.product_id == SKU_HIGH_QTY
    assert master.current_stock == 1
    assert master.units_sold_30d == 288


def test_search_products():
    hits = catalog_service.search_products("47 street", limit=3)
    assert hits
    assert any(h.product_id == SKU_ZERO_QTY for h in hits)


def test_replenishment_recommendation_high_qty():
    rec = catalog_service.get_replenishment_recommendation(SKU_HIGH_QTY)
    assert rec.recommended_quantity == 172


def test_replenishment_recommendation_zero_qty():
    rec = catalog_service.get_replenishment_recommendation(SKU_ZERO_QTY)
    assert rec.recommended_quantity == 0


def test_replenishment_unknown():
    with pytest.raises(ProductNotFoundError):
        catalog_service.get_replenishment_recommendation(SKU_UNKNOWN)


def test_recommendation_context_prices():
    rec = catalog_service.get_replenishment_recommendation(SKU_ZERO_QTY)
    assert rec.context.price is not None


def test_formula_parity():
    master = catalog_service.get_master(SKU_HIGH_QTY)
    calc = calculate_replenishment(
        product_id=master.product_id,
        current_stock=master.current_stock,
        total_units_sold_last_30=master.units_sold_30d,
        lead_time_days=master.lead_time_days,
        safety_stock=master.safety_stock,
    )
    rec = catalog_service.get_replenishment_recommendation(SKU_HIGH_QTY)
    assert rec.calculation.model_dump() == calc.model_dump()
