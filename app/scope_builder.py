from __future__ import annotations

from app.models import AnalyticalScope, QueryInterpretation, ResolutionResult, ResolvedReference
from app.services import metrics
from app.services import scope as scope_svc


def build_scope(
    interpretation: QueryInterpretation,
    resolved: list[ResolvedReference],
) -> AnalyticalScope:
    scope = AnalyticalScope()
    for ref in resolved:
        if ref.match_kind != "group":
            continue
        if ref.scope_dimension == "category" and ref.scope_value:
            scope = scope_svc.add(scope, "category", ref.scope_value)
        elif ref.scope_dimension == "subcategory" and ref.scope_value:
            scope = scope_svc.add(scope, "subcategory", ref.scope_value)

    if interpretation.intent == "inventory_risk":
        scope = scope_svc.add(scope, "health_bucket", metrics.BUCKET_STOCKOUT_RISK)

    for hint in interpretation.filter_hints:
        if hint in ("riesgo", "quiebre", "sin stock", "en falta", "faltante"):
            scope = scope_svc.add(scope, "health_bucket", metrics.BUCKET_STOCKOUT_RISK)

    return scope


def build_resolution_result(interpretation: QueryInterpretation, resolved: list[ResolvedReference]) -> ResolutionResult:
    from app.reference_resolver import disambiguation_options

    blocking = any(r.match_kind == "ambiguous" for r in resolved) and interpretation.confidence == "low"
    if any(r.match_kind == "ambiguous" for r in resolved):
        blocking = True
        interpretation = interpretation.model_copy(update={"confidence": "low"})

    unresolved_all = resolved and all(r.match_kind == "unresolved" for r in resolved)
    if unresolved_all and interpretation.references:
        blocking = True

    scope = build_scope(interpretation, resolved)
    options = disambiguation_options(resolved)

    return ResolutionResult(
        interpretation=interpretation,
        resolved=resolved,
        scope=scope,
        disambiguation_options=options,
        blocking=blocking,
    )
