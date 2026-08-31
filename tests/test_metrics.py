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


def test_metric_contracts_caveats():
    assert "no es una proyección" in metrics.METRIC_CONTRACTS["coverage"].caveat.lower()
    assert "probabilidad" in metrics.METRIC_CONTRACTS["stockout_risk"].caveat.lower()
    assert "dead stock" in metrics.METRIC_CONTRACTS["overstock"].caveat.lower()
    assert "pvp" in metrics.METRIC_CONTRACTS["purchase_value"].caveat.lower()


def test_operational_priority_critical_on_stockout():
    master = ProductMaster(
        product_id="1",
        product_name="A",
        current_stock=5,
        reorder_point=10,
        max_stock=100,
    )
    calc = _calc(recommended_quantity=20, current_stock=5)
    bucket = metrics.health_bucket(master, calc)
    assert metrics.operational_priority(bucket, 20, 0.5) == metrics.PRIORITY_CRITICAL


def test_operational_priority_high_when_coverage_under_horizon():
    assert (
        metrics.operational_priority(metrics.BUCKET_UNDERSTOCK, 10, 3.0)
        == metrics.PRIORITY_HIGH
    )


def test_operational_priority_normal_otherwise():
    assert (
        metrics.operational_priority(metrics.BUCKET_UNDERSTOCK, 10, 12.0)
        == metrics.PRIORITY_NORMAL
    )


def test_purchase_value_uses_price_not_pvp():
    master = ProductMaster(
        product_id="1",
        product_name="A",
        current_stock=10,
        price=4.5,
        pvp=99.0,
    )
    calc = _calc(recommended_quantity=10, current_stock=10)
    row = metrics.sku_analytics_row(master, calc)
    assert row["purchase_cost"] == 4.5
    assert row["estimated_purchase_value"] == 45.0
    assert row["estimated_purchase_value"] != 99.0 * 10

