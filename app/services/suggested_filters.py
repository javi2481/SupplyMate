"""Deterministic suggested filter chips from slice data (no LLM)."""

from __future__ import annotations

from collections import Counter

from app.models import (
    AnalyticalScope,
    InventoryDashboard,
    PurchaseListItem,
    SuggestedFilter,
)
from app.services import metrics

ACTION_FILTER_CATEGORY = "filter_category"
ACTION_FILTER_COVERAGE = "filter_coverage"
ACTION_FILTER_HEALTH = "filter_health"
ACTION_FILTER_SUPPLIER = "filter_supplier"
ACTION_OPEN_SKU = "open_sku"


def suggest_next_filters(
    snap: InventoryDashboard,
    items: list[PurchaseListItem],
    scope: AnalyticalScope,
) -> list[SuggestedFilter]:
    candidates: list[SuggestedFilter] = []
    active_categories = set(scope.categories)
    active_buckets = set(scope.coverage_buckets)
    active_health = set(scope.health_buckets)
    active_suppliers = set(scope.suppliers)

    for bar in snap.by_category:
        if bar.category in active_categories:
            continue
        candidates.append(
            SuggestedFilter(
                action=ACTION_FILTER_CATEGORY,
                args={"category": bar.category},
                label=(
                    f"Ver {bar.category} — {bar.sku_count} SKUs · "
                    f"{bar.recommended_quantity} u."
                ),
            )
        )
        break

    bucket_order = ["0–3 días"] + [
        b.bucket for b in snap.coverage if b.bucket != "0–3 días"
    ]
    seen_buckets: set[str] = set()
    for bucket_name in bucket_order:
        if bucket_name in seen_buckets or bucket_name in active_buckets:
            continue
        seen_buckets.add(bucket_name)
        match = next((b for b in snap.coverage if b.bucket == bucket_name), None)
        if match is None or match.sku_count <= 0:
            continue
        candidates.append(
            SuggestedFilter(
                action=ACTION_FILTER_COVERAGE,
                args={"coverage_bucket": bucket_name},
                label=f"Ver cobertura {bucket_name} — {match.sku_count} SKUs",
            )
        )
        break

    if snap.stockout_risk > 0 and metrics.BUCKET_STOCKOUT_RISK not in active_health:
        candidates.append(
            SuggestedFilter(
                action=ACTION_FILTER_HEALTH,
                args={"health_bucket": metrics.BUCKET_STOCKOUT_RISK},
                label=f"Ver riesgo de quiebre — {snap.stockout_risk} SKUs",
            )
        )

    if items:
        supplier_counts = Counter(
            item.supplier for item in items if (item.supplier or "").strip()
        )
        if supplier_counts:
            top_supplier, count = supplier_counts.most_common(1)[0]
            if top_supplier not in active_suppliers:
                candidates.append(
                    SuggestedFilter(
                        action=ACTION_FILTER_SUPPLIER,
                        args={"supplier": top_supplier},
                        label=f"Ver proveedor {top_supplier} — {count} líneas",
                    )
                )

    if items:
        top = items[0]
        candidates.append(
            SuggestedFilter(
                action=ACTION_OPEN_SKU,
                args={"product_id": top.product_id},
                label=(
                    f"Revisar {top.product_name[:40]} — "
                    f"{top.recommended_quantity} u."
                ),
            )
        )

    out: list[SuggestedFilter] = []
    seen_actions: set[tuple[str, str]] = set()
    for chip in candidates:
        key = (chip.action, str(sorted(chip.args.items())))
        if key in seen_actions:
            continue
        seen_actions.add(key)
        out.append(chip)
        if len(out) >= 3:
            break
    return out
