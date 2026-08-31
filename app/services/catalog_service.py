from __future__ import annotations

from datetime import date

from app.models import (
    AnalyticalScope,
    InventoryDashboard,
    ProductMaster,
    ProductNotFoundError,
    ProductSearchHit,
    PurchaseListItem,
    ReplenishmentRecommendation,
    ReplenishmentSlice,
    SalesHistory,
)
from app.products import resolve_product_id
from app.replenishment import calculate_replenishment
from app.services import dashboard, metrics, suggested_filters
from app.store import SALES_AS_OF, get_store

_sku_rows_cache: list[dict] | None = None


def _sku_analytics_rows() -> list[dict]:
    global _sku_rows_cache
    if _sku_rows_cache is None:
        _sku_rows_cache = dashboard.analytics_rows(tuple(get_store().products.values()))
    return _sku_rows_cache


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
    ranked = [
        row
        for row in _sku_analytics_rows()
        if int(row.get("recommended_quantity") or 0) >= min_quantity
    ]
    ranked.sort(
        key=lambda row: (-int(row["recommended_quantity"]), str(row.get("product_name") or ""))
    )
    items: list[ReplenishmentRecommendation] = []
    store = get_store()
    for row in ranked[:limit]:
        master = store.get_master(row["product_id"])
        calculation = calculate_replenishment(
            product_id=master.product_id,
            current_stock=master.current_stock,
            total_units_sold_last_30=master.units_sold_30d,
            lead_time_days=master.lead_time_days,
            safety_stock=master.safety_stock,
        )
        items.append(ReplenishmentRecommendation.from_master(master, calculation))
    return items


def chat_dashboard(
    limit: int = 25,
    scope: AnalyticalScope | None = None,
) -> tuple[InventoryDashboard, list[PurchaseListItem]]:
    rows = dashboard.filter_rows(_sku_analytics_rows(), scope)
    return dashboard.from_rows(rows), dashboard.purchase_items(rows, limit=limit)


EMPTY_SLICE_EVIDENCE = (
    "Ningún producto cumple estos criterios. "
    "Probá quitar un filtro del breadcrumb o usar **Limpiar filtros**."
)


def format_slice_evidence(
    snap: InventoryDashboard,
    items: list[PurchaseListItem],
    scope: AnalyticalScope,
) -> str:
    if not items:
        return EMPTY_SLICE_EVIDENCE
    total_qty = sum(item.recommended_quantity for item in items)
    lines = [
        f"**{len(items)}** productos en este recorte · **{total_qty}** unidades recomendadas.",
        f"**{snap.skus}** SKUs en el recorte · **{snap.stockout_risk}** en riesgo de quiebre.",
    ]
    if scope.categories:
        lines.append(f"Categorías activas: {', '.join(scope.categories)}.")
    if scope.coverage_buckets:
        lines.append(f"Cobertura activa: {', '.join(scope.coverage_buckets)}.")
    if scope.health_buckets:
        labels = [
            metrics.BUCKET_LABELS.get(h, h) for h in scope.health_buckets
        ]
        lines.append(f"Estado activo: {', '.join(labels)}.")
    if scope.suppliers:
        lines.append(f"Proveedores activos: {', '.join(scope.suppliers)}.")
    if snap.avg_coverage is not None:
        lines.append(f"Cobertura promedio del recorte: **{snap.avg_coverage:.1f} días**.")
    return " ".join(lines)


def replenishment_slice(
    scope: AnalyticalScope | None = None,
    *,
    limit: int = 25,
) -> ReplenishmentSlice:
    active = scope or AnalyticalScope()
    snap, items = chat_dashboard(limit=limit, scope=active)
    evidence = format_slice_evidence(snap, items, active)
    chips = suggested_filters.suggest_next_filters(snap, items, active)
    return ReplenishmentSlice(
        scope=active,
        evidence=evidence,
        dashboard=snap,
        purchase_list=items,
        suggested_filters=chips,
    )


def format_dashboard_answer(
    snap: InventoryDashboard,
    items: list[PurchaseListItem],
) -> str:
    if not items:
        return (
            "Con el stock y las ventas de los últimos 30 días, "
            "no hay productos que requieran reposición para cubrir los próximos 7 días."
        )
    coverage = (
        f"{snap.avg_coverage:.1f} días" if snap.avg_coverage is not None else "—"
    )
    return (
        f"**{snap.stockout_risk}** productos en riesgo de quiebre · "
        f"**{len(items)} productos** para reponer. "
        f"Cobertura promedio: {coverage}."
    )


def format_sales_answer(snap: InventoryDashboard) -> str:
    if not snap.by_sales:
        return "No hay ventas registradas en los últimos 30 días para armar un ranking de categorías."
    lines = ["Estas son las **categorías más vendidas** (unidades, últimos 30 días):\n"]
    for i, row in enumerate(snap.by_sales[:8], 1):
        lines.append(
            f"{i}. **{row.category}** — **{row.units_sold}** unidades ({row.sku_count} productos)"
        )
    return "\n".join(lines)


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
    store = get_store()
    items: list[PurchaseListItem] = []
    for r in recommendations:
        master = store.get_master(r.product_id)
        row = metrics.sku_analytics_row(master, r.calculation)
        items.append(
            PurchaseListItem(
                product_id=row["product_id"],
                barcode=row["barcode"] or "",
                product_name=row["product_name"],
                supplier=row["supplier"] or "",
                category=row["category"] or "",
                subcategory=row["subcategory"] or "",
                current_stock=row["current_stock"],
                reorder_point=row["reorder_point"],
                below_reorder_point=master.below_reorder_point,
                average_daily_demand=row["average_daily_demand"],
                days_of_supply=row["days_of_supply"],
                health_bucket=row["health_bucket"],
                recommended_quantity=row["recommended_quantity"],
            )
        )
    return items


PURCHASE_CSV_HEADERS = (
    "barcode",
    "product_id",
    "product_name",
    "supplier",
    "recommended_quantity",
)


def purchase_list_csv_from_items(items: list[PurchaseListItem]) -> str:
    import csv
    import io

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(PURCHASE_CSV_HEADERS)
    for item in items:
        writer.writerow(
            [
                item.barcode,
                item.product_id,
                item.product_name,
                item.supplier,
                item.recommended_quantity,
            ]
        )
    return buf.getvalue()


def purchase_list_csv(
    limit: int = 25,
    scope: AnalyticalScope | None = None,
) -> str:
    _, items = chat_dashboard(limit=limit, scope=scope)
    return purchase_list_csv_from_items(items)
