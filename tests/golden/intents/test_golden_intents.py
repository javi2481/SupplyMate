import csv
import os
from pathlib import Path

import pytest

from app.agent.intents import match_rule_intent

GOLDEN = Path(__file__).parent / "golden_intents.csv"


def _rows() -> list[dict[str, str]]:
    with GOLDEN.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def test_golden_intents_csv_parses():
    rows = _rows()
    assert len(rows) >= 30
    assert {r["intent"] for r in rows} <= {
        "purchase_list",
        "sales_categories",
        "single_product",
        "unknown",
    }


def test_golden_obvious_rows_match_regex():
    for row in _rows():
        if row["needs_llm"] != "0":
            continue
        if row["intent"] in ("single_product", "unknown"):
            assert match_rule_intent(row["message"]) is None
            continue
        assert match_rule_intent(row["message"]) == row["intent"], row["message"]


def test_golden_hard_rows_are_not_covered_by_regex():
    hard = [r for r in _rows() if r["needs_llm"] == "1"]
    assert hard
    for row in hard:
        if row["intent"] == "unknown":
            continue
        assert match_rule_intent(row["message"]) is None, row["message"]


@pytest.mark.llm
@pytest.mark.asyncio
async def test_groq_classifies_hard_intents():
    if os.getenv("RUN_LLM_EVALS") != "1":
        pytest.skip("set RUN_LLM_EVALS=1 to hit Groq")
    from app.agent.intent_classifier import classify_intent

    hard = [r for r in _rows() if r["needs_llm"] == "1"]
    misses = []
    for row in hard:
        got = await classify_intent(row["message"])
        if got != row["intent"]:
            misses.append((row["message"], row["intent"], got))
    assert misses == []
