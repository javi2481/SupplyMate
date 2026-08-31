import csv
from pathlib import Path

import pytest

from app.models import Reference
from app.query_interpretation import interpret_query_rules
from app.reference_resolver import resolve_single_reference

GOLDEN = Path(__file__).parent / "golden_reference_resolution.csv"


def _load_golden():
    with GOLDEN.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.mark.parametrize("row", _load_golden(), ids=lambda r: r["reference"])
def test_golden_reference_resolution(row):
    ref = Reference(text=row["reference"], kind="product_group")
    resolved = resolve_single_reference(ref)
    assert resolved.match_kind == row["match_kind"], resolved
    if row["scope_dimension"]:
        assert resolved.scope_dimension == row["scope_dimension"]
    if row["scope_value_contains"]:
        assert row["scope_value_contains"] in (resolved.scope_value or "")


def test_jabones_group_has_many_skus():
    resolved = resolve_single_reference(Reference(text="jabones"))
    assert resolved.match_kind == "group"
    assert resolved.sku_count >= 10
    assert resolved.recommended_quantity > 0


def test_shampoo_is_subcategory():
    resolved = resolve_single_reference(Reference(text="shampoo"))
    assert resolved.match_kind == "group"
    assert resolved.scope_dimension == "subcategory"
    assert "Shampoo" in resolved.scope_value


def test_interpret_jabones_purchase():
    interp = interpret_query_rules("¿Cuántos jabones debo comprar?")
    assert interp is not None
    assert interp.intent == "replenishment"
    assert any(r.text == "jabones" for r in interp.references)


def test_interpret_jabones_and_shampoo():
    interp = interpret_query_rules("¿Cuántos jabones y shampoo debo comprar?")
    assert interp is not None
    texts = {r.text for r in interp.references}
    assert "jabones" in texts
    assert "shampoo" in texts


def test_interpret_inventory_risk():
    interp = interpret_query_rules("¿Qué jabones tienen riesgo?")
    assert interp is not None
    assert interp.intent == "inventory_risk"
