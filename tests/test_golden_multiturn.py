import csv
from pathlib import Path

import pytest

from app.query_interpretation import classify_relation, interpret_query_rules
from app.reference_resolver import resolve_references
from app.scope_builder import build_scope, promote_new_query_if_needed

GOLDEN = Path(__file__).parent / "golden_multiturn.csv"


def _load_golden():
    with GOLDEN.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _scope_from_message(message: str):
    interp = interpret_query_rules(message)
    assert interp is not None, message
    resolved = resolve_references(interp)
    interp = promote_new_query_if_needed(interp, resolved, None)
    return build_scope(interp, resolved, None)


@pytest.mark.parametrize("row", _load_golden(), ids=lambda r: r["followup"][:40])
def test_golden_multiturn_refinement(row):
    previous_scope = _scope_from_message(row["previous_message"])
    followup = row["followup"]

    assert classify_relation(followup, previous_scope) == row["expected_relation"]

    interp = interpret_query_rules(followup, previous_scope)
    assert interp is not None
    assert interp.relation == row["expected_relation"]

    resolved = resolve_references(interp)
    interp = promote_new_query_if_needed(interp, resolved, previous_scope)
    scope = build_scope(interp, resolved, previous_scope)

    dim = row["must_keep_scope_dim"]
    value = row["must_keep_scope_value"]
    if dim == "category":
        assert any(value in c for c in scope.categories)
    elif dim == "subcategory":
        assert any(value in s for s in scope.subcategories)
    else:
        pytest.fail(f"unsupported must_keep_scope_dim: {dim}")

    token = row["must_add_name_token"]
    assert token in scope.name_tokens
