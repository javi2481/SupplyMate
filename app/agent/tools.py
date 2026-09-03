from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from agents import RunContextWrapper, function_tool

from app.core.models import Inventory, ReplenishmentParams, SalesHistory, SupplyContext
from app.services import catalog_service


def load_inventory(product_id: str, inventory_csv: Path | None = None) -> Inventory:
    _ = inventory_csv
    master = catalog_service.get_master(product_id)
    return Inventory(product_id=master.product_id, current_stock=master.current_stock)


def load_sales_history(
    product_id: str,
    days: int = 30,
    sales_csv: Path | None = None,
    as_of: date | None = None,
) -> SalesHistory:
    _ = sales_csv
    product_id = catalog_service.resolve_product(product_id)
    return catalog_service.get_sales_history(product_id, days=days, as_of=as_of)


def load_replenishment_params(
    product_id: str,
    params_csv: Path | None = None,
) -> ReplenishmentParams:
    _ = params_csv
    master = catalog_service.get_master(product_id)
    return ReplenishmentParams(
        product_id=master.product_id,
        lead_time_days=master.lead_time_days,
        safety_stock=master.safety_stock,
    )


@function_tool
def get_inventory(ctx: RunContextWrapper[SupplyContext], product_id: str) -> dict[str, Any]:
    """Return current stock. product_id may be a code, barcode, or name fragment."""
    inventory = load_inventory(product_id)
    ctx.context.product_id = inventory.product_id
    ctx.context.inventory = inventory
    return inventory.model_dump()


@function_tool
def get_sales_history(
    ctx: RunContextWrapper[SupplyContext],
    product_id: str,
    days: int = 30,
) -> dict[str, Any]:
    """Return recent sales. product_id may be a code, barcode, or product name."""
    sales = load_sales_history(product_id, days=days)
    ctx.context.product_id = sales.product_id
    ctx.context.sales = sales
    return {
        "product_id": sales.product_id,
        "days": sales.days,
        "total_units_sold": sales.total_units_sold,
        "records": [r.model_dump(mode="json") for r in sales.records],
    }


@function_tool
def get_replenishment_params(
    ctx: RunContextWrapper[SupplyContext],
    product_id: str,
) -> dict[str, Any]:
    """Return lead_time_days and safety_stock. Accepts code, barcode, or name."""
    params = load_replenishment_params(product_id)
    ctx.context.product_id = params.product_id
    ctx.context.params = params
    return params.model_dump()
