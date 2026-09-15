"""Python-only oracle predicates over recorte surfaces."""

from __future__ import annotations

import re

from app.core.models import AnalyticalScope, ChatResponse, ReplenishmentSlice
from app.core.replenishment import HORIZON_DAYS, clamp_horizon_days
from app.services.analytics import catalog_service, dashboard, metrics
from app.services.scoping.suggested_filters import ACTION_DRAFT_OC

_CLAIM_RE = re.compile(
    r"\d+\s*(?:unidades|u\.)|\d+\s*SKUs\s*a\s+reponer",
    re.IGNORECASE,
)


def assert_slice_matches_filter(
    scope: AnalyticalScope,
    slice_data: ReplenishmentSlice,
) -> None:
    """Panel SKU count must equal filter_rows over the same analytics universe."""
    days = clamp_horizon_days(scope.horizon_days or HORIZON_DAYS)
    rows = catalog_service._sku_analytics_rows(days)  # noqa: SLF001 — shared cache
    filtered = dashboard.filter_rows(rows, scope)
    assert slice_data.dashboard.skus == len(filtered), (
        f"dashboard.skus={slice_data.dashboard.skus} != len(filter_rows)={len(filtered)} "
        f"for scope={scope.model_dump()}"
    )


def assert_emptiness_equivalence(slice_data: ReplenishmentSlice) -> None:
    empty_list = len(slice_data.purchase_list) == 0
    empty_skus = slice_data.dashboard.purchase_skus == 0
    empty_units = slice_data.dashboard.recommended_units == 0
    assert empty_list == empty_skus == empty_units, (
        "emptiness must be one fact: "
        f"purchase_list_empty={empty_list}, "
        f"purchase_skus={slice_data.dashboard.purchase_skus}, "
        f"recommended_units={slice_data.dashboard.recommended_units}"
    )


def assert_no_draft_oc_when_empty(slice_data: ReplenishmentSlice) -> None:
    if slice_data.purchase_list:
        return
    actions = [chip.action for chip in slice_data.suggested_filters]
    assert ACTION_DRAFT_OC not in actions, actions
    if slice_data.guidance is not None:
        assert slice_data.guidance.action != "draft_oc", slice_data.guidance


def assert_surface_coherence(response: ChatResponse) -> None:
    """If a response carries a dashboard, it must carry the scope it was computed from."""
    if response.dashboard is not None:
        assert response.scope is not None, (
            f"mode={response.mode!r} has dashboard without scope"
        )


def assert_horizon_echo(scope: AnalyticalScope, expected: int | None) -> None:
    if expected is None:
        return
    assert scope.horizon_days == clamp_horizon_days(expected)


def assert_no_replenishment_claim(answer: str) -> None:
    assert _CLAIM_RE.findall(answer) == [], answer


def is_health_bucket(value: str) -> bool:
    return value in {
        metrics.BUCKET_STOCKOUT_RISK,
        metrics.BUCKET_UNDERSTOCK,
        metrics.BUCKET_OVERSTOCK,
        metrics.BUCKET_HEALTHY,
    }


def is_coverage_bucket(value: str) -> bool:
    return value in set(dashboard.COVERAGE_ORDER)
