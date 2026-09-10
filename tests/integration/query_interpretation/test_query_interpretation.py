from app.core.models import AnalyticalScope
from app.pipeline.query_interpretation import classify_relation, interpret_query_rules


def test_purchase_list_still_root():
    interp = interpret_query_rules("¿Qué productos tengo que comprar?")
    assert interp is not None
    assert interp.intent == "replenishment"
    assert interp.references == []


def test_empty_message_returns_unknown():
    interp = interpret_query_rules("")
    assert interp is not None
    assert interp.intent == "unknown"


def test_top_categories_intent():
    interp = interpret_query_rules("¿Cuáles son las categorías más vendidas?")
    assert interp is not None
    assert interp.intent == "sales_ranking"


def test_todos_is_refinement_with_scope():
    scope = AnalyticalScope(categories=["Pañales"])
    assert classify_relation("todos", scope) == "refinement"
    interp = interpret_query_rules("todos", scope)
    assert interp is not None
    assert interp.relation == "refinement"


def test_purchase_list_with_risk_hint():
    interp = interpret_query_rules("productos en riesgo de quiebre")
    assert interp is not None
    assert interp.intent == "inventory_risk"


def test_solo_xxg_refinement_extracts_size_token():
    scope = AnalyticalScope(categories=["Pañales"])
    interp = interpret_query_rules("solo XXG", scope)
    assert interp is not None
    assert interp.relation == "refinement"
    assert any(r.text == "xxg" for r in interp.references)


def test_refinement_marker_classifies_as_refinement():
    scope = AnalyticalScope(categories=["Pañales"])
    assert classify_relation("solamente xxg", scope) == "refinement"


def test_short_refinement_without_entity_tokens():
    scope = AnalyticalScope(categories=["Pañales"])
    interp = interpret_query_rules("bebé", scope)
    assert interp is not None
    assert interp.relation == "refinement"


def test_criticos_and_coverage_hints():
    from app.pipeline.query_interpretation import extract_coverage_bucket, _extract_filter_hints

    msg = (
        "mostrame los productos críticos de cosmética que tengan "
        "menos de 3 días de cobertura y ordenalos por unidades a pedir"
    )
    assert extract_coverage_bucket(msg) == "0–3 días"
    hints = _extract_filter_hints(msg)
    assert "criticos" in hints
    assert "0–3 días" in hints
    interp = interpret_query_rules(msg)
    assert interp is not None
    assert interp.intent == "inventory_risk"
    assert "0–3 días" in interp.filter_hints
    assert any("cosmetica" in r.text for r in interp.references)


def test_horizon_days_not_confused_with_coverage_band():
    from app.core.models import QueryInterpretation
    from app.pipeline.query_interpretation import (
        enrich_interpretation_from_message,
        extract_coverage_bucket,
        _extract_filter_hints,
    )

    msg = "¿Qué tengo que comprar para los próximos 30 días?"
    assert extract_coverage_bucket(msg) is None
    assert "30+ días" not in _extract_filter_hints(msg)
    poisoned = QueryInterpretation(
        intent="replenishment",
        filter_hints=["30+ días"],
        source="llm",
    )
    cleaned = enrich_interpretation_from_message(poisoned, msg)
    assert "30+ días" not in cleaned.filter_hints


def test_build_scope_applies_coverage_and_criticos():
    from app.core.models import QueryInterpretation, Reference, ResolvedReference
    from app.pipeline.scope_builder import build_scope
    from app.services.analytics import metrics

    interp = QueryInterpretation(
        intent="inventory_risk",
        references=[Reference(text="cosmética", kind="product_group")],
        filter_hints=["criticos", "0–3 días"],
        source="rules",
    )
    resolved = [
        ResolvedReference(
            label="Cosmetica",
            user_text="cosmética",
            match_kind="group",
            scope_dimension="category",
            scope_value="Cosmetica",
            sku_count=10,
        )
    ]
    scope = build_scope(interp, resolved)
    assert scope.categories == ["Cosmetica"]
    assert metrics.BUCKET_STOCKOUT_RISK in scope.health_buckets
    assert "0–3 días" in scope.coverage_buckets
