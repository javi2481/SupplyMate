"""Purchase table columns for live Explore (job-first, no fake trend)."""

from __future__ import annotations

from typing import Any

from app.services.analytics import metrics
from ui import theme

SIGNAL_COLUMN = "Señal"

EXPLORE_COLUMNS = [
    "Prioridad",
    "Producto",
    "Pedir",
    "Cobertura (días)",
    "Stock",
    "Proveedor",
    SIGNAL_COLUMN,
]


def build_explore_rows(purchase_list: list[dict]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in purchase_list:
        bucket = str(item.get("health_bucket") or "")
        dos = item.get("days_of_supply")
        coverage_val = float(dos) if dos is not None else 0.0
        rows.append(
            {
                "Prioridad": metrics.PRIORITY_LABELS.get(
                    str(item.get("operational_priority") or ""),
                    item.get("operational_priority") or "—",
                ),
                "Producto": item.get("product_name", ""),
                "Pedir": int(item.get("recommended_quantity") or 0),
                "Cobertura (días)": min(coverage_val, 30.0),
                "Stock": int(item.get("current_stock") or 0),
                "Proveedor": item.get("supplier", ""),
                SIGNAL_COLUMN: theme.TREND_LABELS.get(bucket, "—"),
            }
        )
    return rows
