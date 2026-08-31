"""Analytical scope: deterministic drill-down filters."""

from __future__ import annotations

from copy import deepcopy

from app.models import AnalyticalScope
from app.store import SALES_AS_OF

_LIMITS: dict[str, int] = {
    "categories": 5,
    "coverage_buckets": 5,
    "health_buckets": 4,
    "suppliers": 5,
}

_FIELD_BY_DIMENSION: dict[str, str] = {
    "category": "categories",
    "coverage_bucket": "coverage_buckets",
    "health_bucket": "health_buckets",
    "supplier": "suppliers",
}


def empty_scope() -> AnalyticalScope:
    return AnalyticalScope()


def reset() -> AnalyticalScope:
    return empty_scope()


def add(scope: AnalyticalScope, dimension: str, value: str) -> AnalyticalScope:
    field = _FIELD_BY_DIMENSION.get(dimension)
    if field is None or not value:
        return scope
    updated = deepcopy(scope)
    current: list[str] = list(getattr(updated, field))
    if value in current:
        return scope
    limit = _LIMITS[field]
    if len(current) >= limit:
        return scope
    current.append(value)
    setattr(updated, field, current)
    return updated


def remove(scope: AnalyticalScope, dimension: str, value: str) -> AnalyticalScope:
    field = _FIELD_BY_DIMENSION.get(dimension)
    if field is None:
        return scope
    updated = deepcopy(scope)
    current: list[str] = list(getattr(updated, field))
    if value not in current:
        return scope
    current.remove(value)
    setattr(updated, field, current)
    return updated


def set_highlight(scope: AnalyticalScope, product_id: str) -> AnalyticalScope:
    updated = deepcopy(scope)
    updated.highlight_product_id = product_id
    return updated


def clear_highlight(scope: AnalyticalScope) -> AnalyticalScope:
    if not scope.highlight_product_id:
        return scope
    updated = deepcopy(scope)
    updated.highlight_product_id = ""
    return updated


def scope_from_query_params(
    *,
    categories: list[str] | None = None,
    coverage_buckets: list[str] | None = None,
    health_buckets: list[str] | None = None,
    suppliers: list[str] | None = None,
    highlight_product_id: str = "",
) -> AnalyticalScope:
    return AnalyticalScope(
        categories=list(categories or []),
        coverage_buckets=list(coverage_buckets or []),
        health_buckets=list(health_buckets or []),
        suppliers=list(suppliers or []),
        highlight_product_id=highlight_product_id or "",
    )


def cache_key(scope: AnalyticalScope) -> str:
    parts = [
        f"as_of={SALES_AS_OF.isoformat()}",
        f"categories={','.join(sorted(scope.categories))}",
        f"coverage={','.join(sorted(scope.coverage_buckets))}",
        f"health={','.join(sorted(scope.health_buckets))}",
        f"suppliers={','.join(sorted(scope.suppliers))}",
        f"highlight={scope.highlight_product_id or ''}",
    ]
    return "|".join(parts)
