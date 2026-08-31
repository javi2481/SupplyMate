import csv
from pathlib import Path

from app.query_interpretation import interpret_query_rules

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
