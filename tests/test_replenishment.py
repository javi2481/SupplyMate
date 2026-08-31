from app.replenishment import calculate_replenishment


def test_average_daily_demand_from_30_day_total():
    result = calculate_replenishment(
        product_id="PROD-001",
        current_stock=170,
        total_units_sold_last_30=750,
        lead_time_days=3,
        safety_stock=50,
    )
    assert result.average_daily_demand == 25.0


def test_stock_target_components():
    result = calculate_replenishment(
        product_id="PROD-001",
        current_stock=170,
        total_units_sold_last_30=750,
        lead_time_days=3,
        safety_stock=50,
    )
    assert result.demand_horizon == 175.0
    assert result.demand_lead_time == 75.0
    assert result.stock_target == 300.0
    assert result.recommended_quantity == 130


def test_recommended_quantity_zero_when_stock_exceeds_target():
    result = calculate_replenishment(
        product_id="PROD-002",
        current_stock=500,
        total_units_sold_last_30=750,
        lead_time_days=3,
        safety_stock=50,
    )
    assert result.stock_target == 300.0
    assert result.recommended_quantity == 0


def test_ceil_rounds_fractional_gap_up():
    result = calculate_replenishment(
        product_id="PROD-FRAC",
        current_stock=10,
        total_units_sold_last_30=125,
        lead_time_days=3,
        safety_stock=10,
    )
    # D=4.166...; horizon=29.166...; lead=12.5; target=51.666...; gap=41.666... → 42
    assert result.recommended_quantity == 42


def test_policy_does_not_use_reorder_point():
    import inspect

    source = inspect.getsource(calculate_replenishment)
    assert "reorder_point" not in source



def test_different_lead_time_triangulation():
    result = calculate_replenishment(
        product_id="PROD-003",
        current_stock=80,
        total_units_sold_last_30=300,
        lead_time_days=4,
        safety_stock=30,
    )
    # avg=10; horizon=70; lead=40; target=140; qty=60
    assert result.average_daily_demand == 10.0
    assert result.recommended_quantity == 60
