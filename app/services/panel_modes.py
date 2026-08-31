"""Ask/Agent panel modes — pure helpers for explore vs commit."""

from __future__ import annotations

from app.models import AnalyticalScope, PanelMode


def effective_scope(
    mode: PanelMode,
    scope: AnalyticalScope,
    frozen_scope: AnalyticalScope | None,
) -> AnalyticalScope:
    if mode == "commit":
        if frozen_scope is None:
            raise ValueError("frozen_scope required for commit mode")
        return frozen_scope
    return scope


def can_export(panel_mode: str) -> bool:
    return panel_mode == "commit"


def scopes_match_filters(a: AnalyticalScope, b: AnalyticalScope) -> bool:
    """Filter dimensions (excluding highlight) must match when entering commit."""
    return (
        sorted(a.categories) == sorted(b.categories)
        and sorted(a.coverage_buckets) == sorted(b.coverage_buckets)
        and sorted(a.health_buckets) == sorted(b.health_buckets)
        and sorted(a.suppliers) == sorted(b.suppliers)
    )


def validate_commit_request(
    mode: PanelMode,
    scope: AnalyticalScope,
    frozen_scope: AnalyticalScope | None,
) -> None:
    if mode != "commit":
        return
    if frozen_scope is None:
        raise ValueError("frozen_scope required for commit mode")
    if not scopes_match_filters(scope, frozen_scope):
        raise ValueError("frozen_scope filter dimensions must match scope")
