"""Pure KPI → scope mutations for Explore controls."""

from __future__ import annotations

from copy import deepcopy

from app.core.models import AnalyticalScope
from app.services.analytics import metrics
from app.services import scope as scope_svc

KPI_PRODUCTS = "products"
KPI_UNDERSTOCK = "understock"
KPI_STOCKOUT_RISK = "stockout_risk"
KPI_COVERAGE = "coverage"


def apply_kpi_action(scope: AnalyticalScope, action: str) -> AnalyticalScope | None:
    """Return a new scope for a count-KPI click, or None for no-op / descriptive KPIs."""
    if action == KPI_COVERAGE:
        return None
    if action == KPI_PRODUCTS:
        return _strip_to_category_core(scope)
    if action == KPI_UNDERSTOCK:
        return scope_svc.add(scope, "health_bucket", metrics.BUCKET_UNDERSTOCK)
    if action == KPI_STOCKOUT_RISK:
        return scope_svc.add(scope, "health_bucket", metrics.BUCKET_STOCKOUT_RISK)
    return None


def _strip_to_category_core(scope: AnalyticalScope) -> AnalyticalScope | None:
    """Keep categories/subcategories; clear health, coverage, tokens, highlight."""
    has_extra = bool(
        scope.coverage_buckets
        or scope.health_buckets
        or scope.suppliers
        or scope.name_tokens
        or scope.highlight_product_id
    )
    if not has_extra:
        return None
    updated = deepcopy(scope)
    updated.coverage_buckets = []
    updated.health_buckets = []
    updated.suppliers = []
    updated.name_tokens = []
    updated.highlight_product_id = ""
    updated.guidance_dismissed = []
    return updated
