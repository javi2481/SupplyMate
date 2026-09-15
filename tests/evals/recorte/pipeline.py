"""Thin call-throughs into the production resolution / slice pipeline."""

from __future__ import annotations

from app.agent.runner import run_supplymate
from app.core.models import AnalyticalScope, ChatResponse, ResolutionResult
from app.pipeline.query_interpretation import interpret_query_rules
from app.pipeline.reference_resolver import resolve_references
from app.pipeline.scope_builder import build_resolution_result, promote_new_query_if_needed
from app.services.analytics import catalog_service


def run_resolution(
    message: str,
    previous_scope: AnalyticalScope | None = None,
) -> ResolutionResult:
    interpretation = interpret_query_rules(message, previous_scope)
    if interpretation is None:
        from app.core.models import QueryInterpretation

        interpretation = QueryInterpretation(intent="unknown")
    resolved = resolve_references(interpretation)
    interpretation = promote_new_query_if_needed(
        interpretation, resolved, previous_scope
    )
    return build_resolution_result(interpretation, resolved, previous_scope)


def run_slice(scope: AnalyticalScope | None = None, *, limit: int = 25):
    return catalog_service.replenishment_slice(scope, limit=limit)


async def run_turn(
    message: str,
    previous_scope: AnalyticalScope | None = None,
) -> ChatResponse:
    """Optional full-turn wrapper — prefer ``run_slice`` in default CI."""
    return await run_supplymate(message, scope=previous_scope)
