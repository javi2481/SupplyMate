from __future__ import annotations

import math

from app.core.models import ReplenishmentResult

HORIZON_DAYS = 7
HISTORY_DAYS = 30
MIN_HORIZON_DAYS = 1
MAX_HORIZON_DAYS = 365

# Periodic review / order-up-to: T = demand during review horizon + demand during
# lead time + explicit safety stock. reorder_point is NOT an input.
POLICY_NAME = "order-up-to"
POLICY_SUMMARY = (
    "Periodic review / order-up-to: target stock = demand(horizon days) "
    "+ demand(lead time) + safety stock. "
    "Recommended qty = max(0, ceil(target − on hand)). "
    "reorder_point is a health alarm, not part of this formula."
)


def clamp_horizon_days(horizon_days: int | None) -> int:
    if horizon_days is None:
        return HORIZON_DAYS
    try:
        value = int(horizon_days)
    except (TypeError, ValueError):
        return HORIZON_DAYS
    return max(MIN_HORIZON_DAYS, min(MAX_HORIZON_DAYS, value))


def calculate_replenishment(
    *,
    product_id: str,
    current_stock: int,
    total_units_sold_last_30: int,
    lead_time_days: int,
    safety_stock: int,
    horizon_days: int = HORIZON_DAYS,
) -> ReplenishmentResult:
    days = clamp_horizon_days(horizon_days)
    average_daily_demand = total_units_sold_last_30 / HISTORY_DAYS
    demand_horizon = average_daily_demand * days
    demand_lead_time = average_daily_demand * lead_time_days
    stock_target = demand_horizon + demand_lead_time + safety_stock
    gap = stock_target - current_stock
    recommended_quantity = max(0, math.ceil(gap)) if gap > 0 else 0

    return ReplenishmentResult(
        product_id=product_id,
        average_daily_demand=average_daily_demand,
        demand_horizon=demand_horizon,
        demand_lead_time=demand_lead_time,
        stock_target=stock_target,
        current_stock=current_stock,
        recommended_quantity=recommended_quantity,
        horizon_days=days,
        history_days=HISTORY_DAYS,
        lead_time_days=lead_time_days,
        safety_stock=safety_stock,
    )
