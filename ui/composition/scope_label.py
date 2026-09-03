"""Compact scope line — not a query-builder breadcrumb."""

from __future__ import annotations

from app.core.models import AnalyticalScope
from app.services.analytics import metrics


def _token_label(token: str) -> str:
    return token.upper() if token.islower() else token


def scope_has_filters(scope: AnalyticalScope) -> bool:
    return bool(
        scope.categories
        or scope.subcategories
        or scope.coverage_buckets
        or scope.health_buckets
        or scope.suppliers
        or scope.name_tokens
        or scope.highlight_product_id
    )


def compact_scope_parts(scope: AnalyticalScope) -> list[str]:
    parts: list[str] = []
    parts.extend(scope.categories)
    parts.extend(scope.subcategories)
    parts.extend(scope.coverage_buckets)
    for health in scope.health_buckets:
        parts.append(metrics.BUCKET_LABELS.get(health, health))
    parts.extend(scope.suppliers)
    parts.extend(_token_label(token) for token in scope.name_tokens)
    if scope.highlight_product_id:
        parts.append(f"SKU {scope.highlight_product_id}")
    return parts or ["Inventario"]


def compact_scope_line(scope: AnalyticalScope) -> str:
    return " · ".join(compact_scope_parts(scope))


def sku_count_caption(from_skus: int | None, to_skus: int | None) -> str:
    if from_skus is None or to_skus is None:
        if to_skus is None:
            return ""
        return f"{to_skus} SKUs"
    return f"{from_skus} → {to_skus} SKUs"
