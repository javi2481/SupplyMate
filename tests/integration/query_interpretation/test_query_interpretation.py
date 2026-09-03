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
