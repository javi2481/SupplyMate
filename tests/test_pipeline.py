from app.models import AnalyticalScope
from app.query_interpretation import interpret_query_rules
from app.reference_resolver import resolve_references
from app.scope_builder import build_scope, promote_new_query_if_needed
from app.services import catalog_service


def _run_pipeline(
    message: str,
    previous: AnalyticalScope | None = None,
) -> tuple[AnalyticalScope, object]:
    interp = interpret_query_rules(message, previous)
    assert interp is not None, message
    resolved = resolve_references(interp)
    interp = promote_new_query_if_needed(interp, resolved, previous)
    scope = build_scope(interp, resolved, previous)
    return scope, interp


def test_pipeline_jabones_replenishment_slice():
    scope, interp = _run_pipeline("¿Cuántos jabones debo comprar?")
    assert interp.intent == "replenishment"
    assert any("Jabon" in c for c in scope.categories)

    slice_data = catalog_service.replenishment_slice(scope, limit=25)
    assert slice_data.dashboard.skus > 1
    assert slice_data.purchase_list
    assert sum(i.recommended_quantity for i in slice_data.purchase_list) > 0
    for item in slice_data.purchase_list:
        assert "Jabon" in item.category


def test_pipeline_panales_then_xxg_refinement():
    root_scope, _ = _run_pipeline("¿Cuántos pañales tengo que comprar?")
    assert any("Pañal" in c for c in root_scope.categories)

    root_slice = catalog_service.replenishment_slice(root_scope, limit=50)
    refined_scope, refined_interp = _run_pipeline(
        "solo XXG",
        root_scope,
    )
    assert refined_interp.relation == "refinement"
    assert any("Pañal" in c for c in refined_scope.categories)
    assert "xxg" in refined_scope.name_tokens

    refined_slice = catalog_service.replenishment_slice(refined_scope, limit=50)
    assert 0 < refined_slice.dashboard.skus < root_slice.dashboard.skus

    names = [item.product_name.lower().split() for item in refined_slice.purchase_list]
    if names:
        assert all("xxg" in parts for parts in names)
        assert all("xxxg" not in parts for parts in names)
