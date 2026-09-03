"""Service layer re-exports (analytics, scope, insight)."""

from __future__ import annotations

from typing import Any

__all__ = [
    "catalog_service",
    "dashboard",
    "insight_cache",
    "insight_validator",
    "metrics",
    "panel_modes",
    "prompt_compiler",
    "scope",
    "scope_sanitize",
    "suggested_filters",
]

_EXPORTS = {
    "catalog_service": "app.services.analytics.catalog_service",
    "dashboard": "app.services.analytics.dashboard",
    "metrics": "app.services.analytics.metrics",
    "panel_modes": "app.services.scoping.panel_modes",
    "scope": "app.services.scoping.mutations",
    "scope_sanitize": "app.services.scoping.scope_sanitize",
    "suggested_filters": "app.services.scoping.suggested_filters",
    "insight_cache": "app.services.insight.insight_cache",
    "insight_validator": "app.services.insight.insight_validator",
    "prompt_compiler": "app.services.insight.prompt_compiler",
}


def __getattr__(name: str) -> Any:
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import importlib

    return importlib.import_module(target)
