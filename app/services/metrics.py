"""Shared analytics metrics — canonical labels for Operation + Analytics."""

from __future__ import annotations

from typing import Literal

from app.models import ProductMaster, ReplenishmentResult

BUCKET_STOCKOUT_RISK = "stockout_risk"
BUCKET_UNDERSTOCK = "understock"
BUCKET_OVERSTOCK = "overstock"
BUCKET_HEALTHY = "healthy"

HealthBucket = Literal["stockout_risk", "understock", "overstock", "healthy"]

LABEL_STOCKOUT_RISK = "Riesgo de quiebre"
LABEL_UNDERSTOCK = "Falta de stock"
LABEL_OVERSTOCK = "Sobrestock"
LABEL_HEALTHY = "Saludable"
LABEL_COVERAGE = "Cobertura"
LABEL_RECOMMENDED_QTY = "Cantidad recomendada"
LABEL_SKUS = "Productos"

BUCKET_LABELS: dict[str, str] = {
    BUCKET_STOCKOUT_RISK: LABEL_STOCKOUT_RISK,
    BUCKET_UNDERSTOCK: LABEL_UNDERSTOCK,
    BUCKET_OVERSTOCK: LABEL_OVERSTOCK,
    BUCKET_HEALTHY: LABEL_HEALTHY,
}


def days_of_supply(current_stock: int, average_daily_demand: float) -> float | None:
    if average_daily_demand <= 0:
        return None
    return current_stock / average_daily_demand


def health_bucket(master: ProductMaster, calculation: ReplenishmentResult) -> HealthBucket:
    qty = calculation.recommended_quantity
    stock = master.current_stock
    if qty > 0:
        if master.reorder_point is not None and stock <= master.reorder_point:
            return BUCKET_STOCKOUT_RISK
        return BUCKET_UNDERSTOCK
    if master.max_stock is not None and stock > master.max_stock:
        return BUCKET_OVERSTOCK
    return BUCKET_HEALTHY


def sku_analytics_row(master: ProductMaster, calculation: ReplenishmentResult) -> dict:
    coverage = days_of_supply(master.current_stock, calculation.average_daily_demand)
    bucket = health_bucket(master, calculation)
    return {
        "product_id": master.product_id,
        "product_name": master.product_name,
        "barcode": master.barcode,
        "supplier": master.supplier,
        "category": master.category,
        "subcategory": master.subcategory,
        "current_stock": master.current_stock,
        "min_stock": master.min_stock,
        "max_stock": master.max_stock,
        "reorder_point": master.reorder_point,
        "units_sold_30d": master.units_sold_30d,
        "average_daily_demand": calculation.average_daily_demand,
        "days_of_supply": coverage,
        "lead_time_days": master.lead_time_days,
        "safety_stock": master.safety_stock,
        "recommended_quantity": calculation.recommended_quantity,
        "health_bucket": bucket,
        "health_label": BUCKET_LABELS[bucket],
        "price": master.price,
        "price_offer": master.price_offer,
    }
