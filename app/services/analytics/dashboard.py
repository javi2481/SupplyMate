"""Inventory dashboard for the Streamlit chat — same metrics as Python replenishment."""

from __future__ import annotations

from collections import defaultdict

from app.core.models import (
    AnalyticalScope,
    CategoryBar,
    CategorySalesBar,
    CoverageBar,
    InventoryDashboard,
    ProductMaster,
    PurchaseListItem,
)
from app.core.replenishment import calculate_replenishment
from app.services.analytics import metrics
from app.pipeline.reference_resolver import name_has_token

COVERAGE_ORDER = ("0–3 días", "3–7 días", "7–14 días", "14–30 días", "30+ días")
MISSING_CATEGORY = "Sin categoría"


def total_recommended_qty(items: list[dict]) -> int:
    return sum(int(item.get("recommended_quantity") or 0) for item in items)


def coverage_bucket(days_of_supply: float | None) -> str | None:
    if days_of_supply is None:
        return None
    if days_of_supply < 3:
        return "0–3 días"
    if days_of_supply < 7:
        return "3–7 días"
    if days_of_supply < 14:
        return "7–14 días"
    if days_of_supply < 30:
        return "14–30 días"
    return "30+ días"


def _row_category(row: dict) -> str:
    name = str(row.get("category") or "").strip()
    return name or MISSING_CATEGORY


def _row_subcategory(row: dict) -> str:
    name = str(row.get("subcategory") or "").strip()
    return name


def filter_rows(rows: list[dict], scope: AnalyticalScope | None) -> list[dict]:
    if scope is None or not any(
        (
            scope.categories,
            scope.subcategories,
            scope.coverage_buckets,
            scope.health_buckets,
            scope.suppliers,
            scope.name_tokens,
        )
    ):
        return list(rows)

    filtered = list(rows)
    if scope.categories or scope.subcategories:
        allowed_cats = set(scope.categories)
        allowed_subs = set(scope.subcategories)
        if allowed_cats and allowed_subs:
            filtered = [
                row
                for row in filtered
                if _row_category(row) in allowed_cats
                or _row_subcategory(row) in allowed_subs
            ]
        elif allowed_cats:
            filtered = [row for row in filtered if _row_category(row) in allowed_cats]
        elif allowed_subs:
            filtered = [
                row for row in filtered if _row_subcategory(row) in allowed_subs
            ]
    if scope.coverage_buckets:
        allowed = set(scope.coverage_buckets)
        filtered = [
            row
            for row in filtered
            if coverage_bucket(row.get("days_of_supply")) in allowed
        ]
    if scope.health_buckets:
        allowed = set(scope.health_buckets)
        filtered = [
            row for row in filtered if str(row.get("health_bucket") or "") in allowed
        ]
    if scope.suppliers:
        allowed = set(scope.suppliers)
        filtered = [
            row
            for row in filtered
            if str(row.get("supplier") or "").strip() in allowed
        ]
    if scope.name_tokens:
        filtered = [
            row
            for row in filtered
            if all(
                name_has_token(str(row.get("product_name") or ""), token)
                for token in scope.name_tokens
            )
        ]
    return filtered


def analytics_rows(products: list[ProductMaster] | tuple[ProductMaster, ...]) -> list[dict]:
    rows: list[dict] = []
    for master in products:
        calculation = calculate_replenishment(
            product_id=master.product_id,
            current_stock=master.current_stock,
            total_units_sold_last_30=master.units_sold_30d,
            lead_time_days=master.lead_time_days,
            safety_stock=master.safety_stock,
        )
        rows.append(metrics.sku_analytics_row(master, calculation))
    return rows


def from_rows(rows: list[dict], *, category_limit: int = 8) -> InventoryDashboard:
    skus = len(rows)
    counts = defaultdict(int)
    coverage_days: list[float] = []
    bucket_counts = {name: 0 for name in COVERAGE_ORDER}
    category_qty: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    sales_qty: dict[str, list[int]] = defaultdict(lambda: [0, 0])

    for row in rows:
        bucket = str(row.get("health_bucket") or "")
        counts[bucket] += 1
        coverage = row.get("days_of_supply")
        if coverage is not None:
            coverage_days.append(float(coverage))
            label = coverage_bucket(float(coverage))
            if label:
                bucket_counts[label] += 1
        name = str(row.get("category") or "").strip() or MISSING_CATEGORY
        sold = int(row.get("units_sold_30d") or 0)
        sales_qty[name][0] += sold
        sales_qty[name][1] += 1
        qty = int(row.get("recommended_quantity") or 0)
        if qty > 0:
            category_qty[name][0] += qty
            category_qty[name][1] += 1

    ranked = sorted(category_qty.items(), key=lambda pair: (-pair[1][0], pair[0]))
    ranked_sales = sorted(
        ((name, vals) for name, vals in sales_qty.items() if vals[0] > 0),
        key=lambda pair: (-pair[1][0], pair[0]),
    )
    avg = (sum(coverage_days) / len(coverage_days)) if coverage_days else None
    value_parts = [
        float(row["estimated_purchase_value"])
        for row in rows
        if int(row.get("recommended_quantity") or 0) > 0
        and row.get("estimated_purchase_value") is not None
    ]
    return InventoryDashboard(
        skus=skus,
        stockout_risk=counts[metrics.BUCKET_STOCKOUT_RISK],
        understock=counts[metrics.BUCKET_UNDERSTOCK],
        overstock=counts[metrics.BUCKET_OVERSTOCK],
        healthy=counts[metrics.BUCKET_HEALTHY],
        avg_coverage=avg,
        estimated_purchase_value=sum(value_parts) if value_parts else None,
        by_category=[
            CategoryBar(category=name, recommended_quantity=qty, sku_count=n)
            for name, (qty, n) in ranked[:category_limit]
        ],
        by_sales=[
            CategorySalesBar(category=name, units_sold=sold, sku_count=n)
            for name, (sold, n) in ranked_sales[:category_limit]
        ],
        coverage=[
            CoverageBar(bucket=name, sku_count=bucket_counts[name]) for name in COVERAGE_ORDER
        ],
    )


def purchase_items(rows: list[dict], limit: int = 25) -> list[PurchaseListItem]:
    needed = [row for row in rows if int(row.get("recommended_quantity") or 0) > 0]
    needed.sort(
        key=lambda row: (
            metrics.PRIORITY_RANK.get(str(row.get("operational_priority") or ""), 9),
            -int(row.get("recommended_quantity") or 0),
            str(row.get("product_name") or ""),
        )
    )
    items: list[PurchaseListItem] = []
    for row in needed[:limit]:
        cost = row.get("purchase_cost")
        value = row.get("estimated_purchase_value")
        items.append(
            PurchaseListItem(
                product_id=str(row.get("product_id") or ""),
                barcode=str(row.get("barcode") or ""),
                product_name=str(row.get("product_name") or ""),
                supplier=str(row.get("supplier") or ""),
                category=str(row.get("category") or ""),
                subcategory=str(row.get("subcategory") or ""),
                current_stock=int(row.get("current_stock") or 0),
                reorder_point=row.get("reorder_point"),
                below_reorder_point=bool(row.get("below_reorder_point")),
                average_daily_demand=float(row.get("average_daily_demand") or 0),
                days_of_supply=row.get("days_of_supply"),
                health_bucket=str(row.get("health_bucket") or ""),
                recommended_quantity=int(row.get("recommended_quantity") or 0),
                operational_priority=str(row.get("operational_priority") or metrics.PRIORITY_NORMAL),
                purchase_cost=float(cost) if cost is not None else None,
                estimated_purchase_value=float(value) if value is not None else None,
            )
        )
    return items
