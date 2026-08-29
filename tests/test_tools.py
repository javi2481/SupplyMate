import pytest

from app.models import ProductNotFoundError
from app.products import resolve_from_message, resolve_product_id
from app.tools import (
    load_inventory,
    load_replenishment_params,
    load_sales_history,
)
from tests.catalog_ids import SKU_HIGH_QTY, SKU_SAMPLE, SKU_UNKNOWN, SKU_ZERO_QTY


def test_load_inventory_valid_product():
    inv = load_inventory(SKU_SAMPLE)
    assert inv.product_id == SKU_SAMPLE
    assert inv.current_stock >= 0


def test_load_inventory_by_name_fragment():
    inv = load_inventory("47 STREET AURA")
    assert inv.product_id == SKU_ZERO_QTY


def test_load_inventory_unknown_product():
    with pytest.raises(ProductNotFoundError) as exc:
        load_inventory(SKU_UNKNOWN)
    assert SKU_UNKNOWN in exc.value.product_id


def test_load_sales_history_valid_product():
    sales = load_sales_history(SKU_HIGH_QTY, days=30)
    assert sales.product_id == SKU_HIGH_QTY
    assert sales.days == 30
    assert len(sales.records) == 30
    assert sales.total_units_sold > 0


def test_load_sales_history_unknown_product():
    with pytest.raises(ProductNotFoundError):
        load_sales_history(SKU_UNKNOWN, days=30)


def test_load_replenishment_params_valid():
    params = load_replenishment_params(SKU_HIGH_QTY)
    assert params.product_id == SKU_HIGH_QTY
    assert params.lead_time_days >= 1
    assert params.safety_stock >= 0


def test_load_replenishment_params_unknown():
    with pytest.raises(ProductNotFoundError):
        load_replenishment_params(SKU_UNKNOWN)


def test_resolve_product_id_by_code():
    assert resolve_product_id(SKU_HIGH_QTY) == SKU_HIGH_QTY
    assert resolve_product_id(SKU_ZERO_QTY) == SKU_ZERO_QTY


def test_resolve_product_id_by_name():
    assert resolve_product_id("47 street aura") == SKU_ZERO_QTY
    assert resolve_product_id(SKU_HIGH_QTY) == SKU_HIGH_QTY


def test_resolve_from_message_by_code():
    assert resolve_from_message(f"cuanto pedir de {SKU_HIGH_QTY}?") == SKU_HIGH_QTY
    assert resolve_from_message("pedir 8141600") == SKU_ZERO_QTY
