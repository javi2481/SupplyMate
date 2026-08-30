"""Tests for shared analytics metrics (Strict TDD)."""

from __future__ import annotations

from app.models import ProductMaster, ReplenishmentResult
from app.services import metrics


def _calc(**kwargs) -> ReplenishmentResult:
    defaults = dict(
        product_id="X",
        average_daily_demand=1.0,
        demand_horizon=7.0,
        demand_lead_time=3.0,
        stock_target=20.0,
        current_stock=10,
        recommended_quantity=10,
        lead_time_days=3,
        safety_stock=5,
    )
    defaults.update(kwargs)
    return ReplenishmentResult(**defaults)


def test_days_of_supply_when_demand_positive():
    assert metrics.days_of_supply(30, 10.0) == 3.0


def test_days_of_supply_none_when_zero_demand():
    assert metrics.days_of_supply(30, 0.0) is None


def test_days_of_supply_triangulation():
    assert metrics.days_of_supply(15, 2.5) == 6.0


def test_health_bucket_stockout_risk():
    master = ProductMaster(
        product_id="1",
        product_name="A",
        current_stock=5,
        reorder_point=10,
        max_stock=100,
    )
    assert metrics.health_bucket(master, _calc(recommended_quantity=20, current_stock=5)) == (
        metrics.BUCKET_STOCKOUT_RISK
    )


def test_health_bucket_understock():
    master = ProductMaster(
        product_id="1",
        product_name="A",
        current_stock=50,
        reorder_point=10,
        max_stock=100,
    )
    assert metrics.health_bucket(master, _calc(recommended_quantity=5, current_stock=50)) == (
        metrics.BUCKET_UNDERSTOCK
    )


def test_health_bucket_overstock():
    master = ProductMaster(
        product_id="1",
        product_name="A",
        current_stock=200,
        reorder_point=10,
        max_stock=100,
    )
    assert metrics.health_bucket(master, _calc(recommended_quantity=0, current_stock=200)) == (
        metrics.BUCKET_OVERSTOCK
    )


def test_health_bucket_healthy():
    master = ProductMaster(
        product_id="1",
        product_name="A",
        current_stock=40,
        reorder_point=10,
        max_stock=100,
    )
    assert metrics.health_bucket(master, _calc(recommended_quantity=0, current_stock=40)) == (
        metrics.BUCKET_HEALTHY
    )


def test_canonical_labels():
    assert metrics.LABEL_STOCKOUT_RISK == "Riesgo de quiebre"
    assert metrics.LABEL_UNDERSTOCK == "Falta de stock"
    assert metrics.LABEL_OVERSTOCK == "Sobrestock"
    assert metrics.LABEL_HEALTHY == "Saludable"
    assert metrics.LABEL_COVERAGE == "Cobertura"
    assert metrics.LABEL_RECOMMENDED_QTY == "Cantidad recomendada"
