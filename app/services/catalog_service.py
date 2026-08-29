from __future__ import annotations

from datetime import date

from app.models import (
    ProductMaster,
    ProductNotFoundError,
    ProductSearchHit,
    PurchaseListItem,
    ReplenishmentRecommendation,
    SalesHistory,
)
from app.products import resolve_product_id
from app.replenishment import calculate_replenishment
from app.store import SALES_AS_OF, get_store


def resolve_product(query: str) -> str:
    return resolve_product_id(query)


def get_master(product_id: str) -> ProductMaster:
    product_id = resolve_product_id(product_id)
    return get_store().get_master(product_id)


def search_products(query: str, limit: int = 10) -> list[ProductSearchHit]:
    return get_store().search(query, limit=limit)


def get_sales_history(
    product_id: str,
    days: int = 30,
    as_of: date | None = None,
) -> SalesHistory:
    product_id = resolve_product_id(product_id)
    return get_store().sales_history(product_id, days=days, as_of=as_of or SALES_AS_OF)


def get_replenishment_recommendation(product_id: str) -> ReplenishmentRecommendation:
    product_id = resolve_product_id(product_id)
    master = get_store().get_master(product_id)
    calculation = calculate_replenishment(
        product_id=master.product_id,
        current_stock=master.current_stock,
        total_units_sold_last_30=master.units_sold_30d,
        lead_time_days=master.lead_time_days,
        safety_stock=master.safety_stock,
    )
    return ReplenishmentRecommendation.from_master(master, calculation)


def get_replenishment_by_query(query: str) -> ReplenishmentRecommendation:
    product_id = resolve_product_id(query)
    return get_replenishment_recommendation(product_id)


def safe_resolve(query: str) -> str | None:
    try:
        return resolve_product_id(query)
    except ProductNotFoundError:
        return None


def list_purchase_recommendations(
    limit: int = 25,
    min_quantity: int = 1,
) -> list[ReplenishmentRecommendation]:
    """All SKUs with recommended_quantity >= min_quantity, sorted desc."""
    store = get_store()
    results: list[ReplenishmentRecommendation] = []
    for master in store.products.values():
        calculation = calculate_replenishment(
            product_id=master.product_id,
            current_stock=master.current_stock,
            total_units_sold_last_30=master.units_sold_30d,
            lead_time_days=master.lead_time_days,
            safety_stock=master.safety_stock,
        )
        if calculation.recommended_quantity >= min_quantity:
            results.append(ReplenishmentRecommendation.from_master(master, calculation))
    results.sort(key=lambda r: (-r.recommended_quantity, r.product_name))
    return results[:limit]


def format_purchase_list_answer(items: list[ReplenishmentRecommendation]) -> str:
    if not items:
        return (
            "Con el stock y las ventas de los últimos 30 días, "
            "no hay productos que requieran reposición para cubrir los próximos 7 días."
        )
    lines = [
        f"Estos son los **{len(items)} productos** con mayor necesidad de reposición:\n"
    ]
    for i, rec in enumerate(items, 1):
        lines.append(
            f"{i}. **{rec.product_name}** — pedir **{rec.recommended_quantity}** unidades"
        )
    lines.append(
        "\nLas cantidades las calculó el sistema según ventas, stock, lead time y stock de seguridad."
    )
    return "\n".join(lines)


def purchase_list_items(
    recommendations: list[ReplenishmentRecommendation],
) -> list[PurchaseListItem]:
    return [
        PurchaseListItem(
            product_name=r.product_name,
            recommended_quantity=r.recommended_quantity,
        )
        for r in recommendations
    ]
