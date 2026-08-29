from __future__ import annotations

from app.models import ReplenishmentResult

HORIZON_DAYS = 7
HISTORY_DAYS = 30


def calculate_replenishment(
    *,
    product_id: str,
    current_stock: int,
    total_units_sold_last_30: int,
    lead_time_days: int,
    safety_stock: int,
) -> ReplenishmentResult:
    average_daily_demand = total_units_sold_last_30 / HISTORY_DAYS
    demand_horizon = average_daily_demand * HORIZON_DAYS
    demand_lead_time = average_daily_demand * lead_time_days
    stock_target = demand_horizon + demand_lead_time + safety_stock
    recommended_quantity = max(0, int(stock_target - current_stock))

    return ReplenishmentResult(
        product_id=product_id,
        average_daily_demand=average_daily_demand,
        demand_horizon=demand_horizon,
        demand_lead_time=demand_lead_time,
        stock_target=stock_target,
        current_stock=current_stock,
        recommended_quantity=recommended_quantity,
        horizon_days=HORIZON_DAYS,
        history_days=HISTORY_DAYS,
        lead_time_days=lead_time_days,
        safety_stock=safety_stock,
    )
