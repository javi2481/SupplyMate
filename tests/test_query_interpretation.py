import csv
from pathlib import Path

from app.models import AnalyticalScope
from app.query_interpretation import classify_relation, interpret_query_rules

GOLDEN = Path(__file__).parent / "golden_query_interpretation.csv"


def _load_golden():
    with GOLDEN.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_golden_query_interpretation_rules():
    for row in _load_golden():
        if row["confidence"] == "low":
            continue
        interp = interpret_query_rules(row["message"])
        assert interp is not None, row["message"]
        assert interp.intent == row["intent"], row["message"]
        if row["references"]:
            expected = row["references"].split("|")
            texts = {r.text for r in interp.references}
            for exp in expected:
                assert exp in texts, (row["message"], texts)


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
