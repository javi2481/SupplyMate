"""Catalog-backed facets for the current replenishment slice."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from app.guidance_tokens import GUIDE_SKU_THRESHOLD, size_tokens_from_skus
from app.models import AnalyticalScope, InventoryDashboard, PurchaseListItem
from app.missions import MissionEdge, mission_neighbors
from app.services import metrics
from app.services import catalog_service
from app.store import get_store


@dataclass
class SliceFacets:
    sku_count: int = 0
    purchase_line_count: int = 0
    subcategories: list[tuple[str, int]] = field(default_factory=list)
    size_tokens: list[str] = field(default_factory=list)
    stockout_count: int = 0
    stockout_subset: bool = False
    mission_neighbors: list[MissionEdge] = field(default_factory=list)


def list_slice_facets(
    scope: AnalyticalScope,
    dashboard: InventoryDashboard,
    purchase_items: list[PurchaseListItem],
) -> SliceFacets:
    rows = catalog_service.scoped_analytics_rows(scope)
    sku_ids = [str(r["product_id"]) for r in rows]
    sku_count = dashboard.skus or len(sku_ids)

    sub_counts: Counter[str] = Counter()
    store = get_store()
    active_subs = set(scope.subcategories)
    for pid in sku_ids:
        try:
            master = store.get_master(pid)
        except Exception:
            continue
        sub = (master.subcategory or "").strip()
        if not sub or sub in active_subs:
            continue
        sub_counts[sub] += 1

    subcategories = [
        (name, count) for name, count in sub_counts.most_common() if count >= 1
    ]

    sizes = size_tokens_from_skus(sku_ids)
    stockout = int(dashboard.stockout_risk or 0)
    stockout_subset = (
        stockout > 0
        and metrics.BUCKET_STOCKOUT_RISK not in scope.health_buckets
        and stockout < sku_count
    )

    neighbors = mission_neighbors(scope) if _mission_anchor_ready(scope) else []

    return SliceFacets(
        sku_count=sku_count,
        purchase_line_count=len(purchase_items),
        subcategories=subcategories,
        size_tokens=sizes,
        stockout_count=stockout,
        stockout_subset=stockout_subset,
        mission_neighbors=neighbors,
    )


def _mission_anchor_ready(scope: AnalyticalScope) -> bool:
    if "Pañales P/Bebes" in scope.subcategories:
        return True
    return False
