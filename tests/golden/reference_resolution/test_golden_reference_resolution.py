import csv
from pathlib import Path

import pytest

from app.core.models import Reference
from app.pipeline.reference_resolver import resolve_single_reference

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
