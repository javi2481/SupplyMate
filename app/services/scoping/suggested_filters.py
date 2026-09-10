"""Deterministic suggested filter chips from slice data (no LLM)."""

from __future__ import annotations

from collections import Counter

from app.core.models import (
    AnalyticalScope,
    InventoryDashboard,
    PurchaseListItem,
    SuggestedFilter,
)
from app.services.analytics import metrics

ACTION_FILTER_CATEGORY = "filter_category"
ACTION_FILTER_COVERAGE = "filter_coverage"
ACTION_FILTER_HEALTH = "filter_health"
ACTION_FILTER_SUPPLIER = "filter_supplier"
ACTION_FILTER_NAME_TOKEN = "filter_name_token"
ACTION_OPEN_SKU = "open_sku"
ACTION_DRAFT_OC = "draft_oc"

MAX_CHIPS = 6


def _label_category(category: str) -> str:
    return f"¿Qué hay en {category}?"


def _label_coverage(bucket: str) -> str:
    return f"¿Cobertura {bucket}?"


def _label_sku(name: str) -> str:
    return f"¿Cuánto pedir de {name[:32]}?"


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

    unused_cats = [bar for bar in snap.by_category if bar.category not in active_categories]
    for bar in unused_cats[:2]:
        candidates.append(
            SuggestedFilter(
                action=ACTION_FILTER_CATEGORY,
                args={"category": bar.category},
                label=_label_category(bar.category),
            )
        )

    preferred = next((b for b in snap.coverage if b.bucket == "0–3 días" and b.sku_count > 0), None)
    coverage_pick = None
    if preferred is not None and preferred.bucket not in active_buckets:
        coverage_pick = preferred
    else:
        for bar in snap.coverage:
            if bar.sku_count <= 0 or bar.bucket in active_buckets:
                continue
            coverage_pick = bar
            break
    if coverage_pick is not None:
        candidates.append(
            SuggestedFilter(
                action=ACTION_FILTER_COVERAGE,
                args={"coverage_bucket": coverage_pick.bucket},
                label=_label_coverage(coverage_pick.bucket),
            )
        )

    if snap.stockout_risk > 0 and metrics.BUCKET_STOCKOUT_RISK not in active_health:
        candidates.append(
            SuggestedFilter(
                action=ACTION_FILTER_HEALTH,
                args={"health_bucket": metrics.BUCKET_STOCKOUT_RISK},
                label="¿Riesgo de quiebre?",
            )
        )

    if snap.overstock > 0 and metrics.BUCKET_OVERSTOCK not in active_health:
        candidates.append(
            SuggestedFilter(
                action=ACTION_FILTER_HEALTH,
                args={"health_bucket": metrics.BUCKET_OVERSTOCK},
                label="¿Hay sobrestock?",
            )
        )

    if items:
        supplier_counts = Counter(
            item.supplier for item in items if (item.supplier or "").strip()
        )
        if supplier_counts:
            top_supplier, _count = supplier_counts.most_common(1)[0]
            if top_supplier not in active_suppliers:
                candidates.append(
                    SuggestedFilter(
                        action=ACTION_FILTER_SUPPLIER,
                        args={"supplier": top_supplier},
                        label=f"¿Qué pide {top_supplier}?",
                    )
                )

    if items:
        top = items[0]
        candidates.append(
            SuggestedFilter(
                action=ACTION_OPEN_SKU,
                args={"product_id": top.product_id},
                label=_label_sku(top.product_name),
            )
        )

    recorte_qty = snap.recommended_units or sum(item.recommended_quantity for item in items)
    if recorte_qty > 0:
        candidates.append(
            SuggestedFilter(
                action=ACTION_DRAFT_OC,
                args={},
                label="¿Armar la OC?",
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
        if len(out) >= MAX_CHIPS:
            break
    return out
