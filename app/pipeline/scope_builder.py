from __future__ import annotations

from app.core.models import AnalyticalScope, QueryInterpretation, ResolutionResult, ResolvedReference
from app.services.analytics import metrics
from app.services.scoping import scope as scope_svc
from app.pipeline.query_interpretation import _scope_empty


def promote_new_query_if_needed(
    interpretation: QueryInterpretation,
    resolved: list[ResolvedReference],
    previous: AnalyticalScope | None,
) -> QueryInterpretation:
    """A distinct category/subcategory is a new analysis, not a refinement."""
    if interpretation.relation != "refinement" or _scope_empty(previous):
        return interpretation
    from app.guidance.missions import is_complement_target

    prev = previous or AnalyticalScope()
    for ref in resolved:
        if ref.match_kind != "group":
            continue
        if ref.scope_dimension == "category" and ref.scope_value:
            if ref.scope_value not in prev.categories:
                return interpretation.model_copy(update={"relation": "new_query"})
        if ref.scope_dimension == "subcategory" and ref.scope_value:
            if ref.scope_value not in prev.subcategories:
                if is_complement_target(
                    prev, dimension="subcategory", value=ref.scope_value
                ):
                    continue
                return interpretation.model_copy(update={"relation": "new_query"})
        for token in ref.name_tokens:
            if token not in prev.name_tokens:
                if is_complement_target(prev, dimension="name_token", value=token):
                    continue
                if ref.scope_dimension == "subcategory":
                    return interpretation.model_copy(update={"relation": "new_query"})
    return interpretation


def build_scope(
    interpretation: QueryInterpretation,
    resolved: list[ResolvedReference],
    previous: AnalyticalScope | None = None,
) -> AnalyticalScope:
    if interpretation.relation == "refinement" and not _scope_empty(previous):
        scope = previous.model_copy(deep=True)  # type: ignore[union-attr]
    else:
        scope = AnalyticalScope()
    for ref in resolved:
        if ref.match_kind != "group":
            continue
        if ref.scope_dimension == "category" and ref.scope_value:
            scope = scope_svc.add(scope, "category", ref.scope_value)
        elif ref.scope_dimension == "subcategory" and ref.scope_value:
            scope = scope_svc.add(scope, "subcategory", ref.scope_value)
        for token in ref.name_tokens:
            scope = scope_svc.add(scope, "name_token", token)

    if interpretation.intent == "inventory_risk":
        scope = scope_svc.add(scope, "health_bucket", metrics.BUCKET_STOCKOUT_RISK)

    for hint in interpretation.filter_hints:
        if hint in ("riesgo", "quiebre", "sin stock", "en falta", "faltante"):
            scope = scope_svc.add(scope, "health_bucket", metrics.BUCKET_STOCKOUT_RISK)

    return scope


def build_resolution_result(
    interpretation: QueryInterpretation,
    resolved: list[ResolvedReference],
    previous: AnalyticalScope | None = None,
) -> ResolutionResult:
    from app.pipeline.reference_resolver import disambiguation_options

    blocking = any(r.match_kind == "ambiguous" for r in resolved) and interpretation.confidence == "low"
    if any(r.match_kind == "ambiguous" for r in resolved):
        blocking = True
        interpretation = interpretation.model_copy(update={"confidence": "low"})

    unresolved_all = resolved and all(r.match_kind == "unresolved" for r in resolved)
    if unresolved_all and interpretation.references:
        blocking = True

    todos = any(r.text.strip().lower() == "todos" for r in interpretation.references)
    if todos and interpretation.relation == "refinement":
        blocking = False
        scope = previous.model_copy(deep=True) if previous else AnalyticalScope()
        return ResolutionResult(
            interpretation=interpretation,
            resolved=resolved,
            scope=scope,
            disambiguation_options=[],
            blocking=False,
        )

    scope = build_scope(interpretation, resolved, previous)
    options = disambiguation_options(resolved)

    return ResolutionResult(
        interpretation=interpretation,
        resolved=resolved,
        scope=scope,
        disambiguation_options=options,
        blocking=blocking,
    )

