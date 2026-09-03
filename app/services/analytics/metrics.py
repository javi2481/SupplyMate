"""Shared analytics metrics — canonical labels, contracts, and row builders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.core.models import ProductMaster, ReplenishmentResult
from app.core.replenishment import HORIZON_DAYS, POLICY_SUMMARY

BUCKET_STOCKOUT_RISK = "stockout_risk"
BUCKET_UNDERSTOCK = "understock"
BUCKET_OVERSTOCK = "overstock"
BUCKET_HEALTHY = "healthy"

HealthBucket = Literal["stockout_risk", "understock", "overstock", "healthy"]
OperationalPriority = Literal["critical", "high", "normal"]

PRIORITY_CRITICAL: OperationalPriority = "critical"
PRIORITY_HIGH: OperationalPriority = "high"
PRIORITY_NORMAL: OperationalPriority = "normal"

PRIORITY_RANK = {
    PRIORITY_CRITICAL: 0,
    PRIORITY_HIGH: 1,
    PRIORITY_NORMAL: 2,
}

LABEL_STOCKOUT_RISK = "Riesgo de quiebre"
LABEL_UNDERSTOCK = "Falta de stock"
LABEL_OVERSTOCK = "Sobrestock"
LABEL_HEALTHY = "Saludable"
LABEL_COVERAGE = "Cobertura"
LABEL_RECOMMENDED_QTY = "Cantidad recomendada"
LABEL_SKUS = "Productos"
LABEL_PURCHASE_VALUE = "Valor estimado"
LABEL_PRIORITY = "Prioridad"
LABEL_REORDER_POINT = "Punto de reorden"
LABEL_PURCHASE_COST = "Costo de compra"

BUCKET_LABELS: dict[str, str] = {
    BUCKET_STOCKOUT_RISK: LABEL_STOCKOUT_RISK,
    BUCKET_UNDERSTOCK: LABEL_UNDERSTOCK,
    BUCKET_OVERSTOCK: LABEL_OVERSTOCK,
    BUCKET_HEALTHY: LABEL_HEALTHY,
}

PRIORITY_LABELS: dict[str, str] = {
    PRIORITY_CRITICAL: "Crítica",
    PRIORITY_HIGH: "Alta",
    PRIORITY_NORMAL: "Normal",
}

ROP_CAPTION = "Alarma de salud; no entra en la cantidad a pedir."


@dataclass(frozen=True)
class MetricContract:
    key: str
    label: str
    rule: str
    unit: str
    caveat: str


METRIC_CONTRACTS: dict[str, MetricContract] = {
    "coverage": MetricContract(
        key="coverage",
        label=LABEL_COVERAGE,
        rule="current_stock / average_daily_demand (últimos 30 días)",
        unit="días",
        caveat="Aproximación bajo demanda media constante; no es una proyección temporal.",
    ),
    "stockout_risk": MetricContract(
        key="stockout_risk",
        label=LABEL_STOCKOUT_RISK,
        rule="recommended_quantity > 0 AND current_stock <= reorder_point",
        unit="SKUs",
        caveat="Regla operacional, no una probabilidad estadística de quiebre.",
    ),
    "understock": MetricContract(
        key="understock",
        label=LABEL_UNDERSTOCK,
        rule="recommended_quantity > 0 AND not stockout_risk",
        unit="SKUs",
        caveat="Hay que reponer según la política order-up-to; el stock aún está sobre el ROP.",
    ),
    "overstock": MetricContract(
        key="overstock",
        label=LABEL_OVERSTOCK,
        rule="recommended_quantity == 0 AND current_stock > max_stock",
        unit="SKUs",
        caveat="No es dead stock ni mercadería lenta; solo supera el máximo declarado.",
    ),
    "recommended_qty": MetricContract(
        key="recommended_qty",
        label=LABEL_RECOMMENDED_QTY,
        rule=POLICY_SUMMARY,
        unit="unidades",
        caveat="El LLM no calcula ni altera este número.",
    ),
    "reorder_point": MetricContract(
        key="reorder_point",
        label=LABEL_REORDER_POINT,
        rule="Umbral heredado de la columna de quiebre del catálogo",
        unit="unidades",
        caveat=ROP_CAPTION,
    ),
    "purchase_value": MetricContract(
        key="purchase_value",
        label=LABEL_PURCHASE_VALUE,
        rule="recommended_quantity × purchase_cost (ProductMaster.price)",
        unit="moneda del catálogo",
        caveat="Usa el precio de lista, no el PVP.",
    ),
}


def metric_prompt_block() -> str:
    lines = ["Contratos de métricas (no inventes otras interpretaciones):"]
    for contract in METRIC_CONTRACTS.values():
        lines.append(
            f"- {contract.label}: {contract.rule}. Caveat: {contract.caveat}"
        )
    return "\n".join(lines)


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


def operational_priority(
    bucket: HealthBucket,
    recommended_quantity: int,
    coverage: float | None,
) -> OperationalPriority:
    if bucket == BUCKET_STOCKOUT_RISK:
        return PRIORITY_CRITICAL
    if recommended_quantity > 0 and coverage is not None and coverage < HORIZON_DAYS:
        return PRIORITY_HIGH
    return PRIORITY_NORMAL


def purchase_cost(master: ProductMaster) -> float | None:
    """Acquisition list price. Never PVP."""
    if master.price is None:
        return None
    return float(master.price)


def estimated_purchase_value(qty: int, cost: float | None) -> float | None:
    if cost is None:
        return None
    return qty * cost


def sku_analytics_row(master: ProductMaster, calculation: ReplenishmentResult) -> dict:
    coverage = days_of_supply(master.current_stock, calculation.average_daily_demand)
    bucket = health_bucket(master, calculation)
    cost = purchase_cost(master)
    qty = calculation.recommended_quantity
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
        "below_reorder_point": master.below_reorder_point,
        "units_sold_30d": master.units_sold_30d,
        "average_daily_demand": calculation.average_daily_demand,
        "days_of_supply": coverage,
        "lead_time_days": master.lead_time_days,
        "safety_stock": master.safety_stock,
        "recommended_quantity": qty,
        "health_bucket": bucket,
        "health_label": BUCKET_LABELS[bucket],
        "operational_priority": operational_priority(bucket, qty, coverage),
        "price": master.price,
        "price_offer": master.price_offer,
        "purchase_cost": cost,
        "estimated_purchase_value": estimated_purchase_value(qty, cost),
    }
