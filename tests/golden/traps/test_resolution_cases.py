"""Resolution eval cases — vernacular/taxonomy contracts without growing legacy goldens."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from app.core.models import Reference
from app.pipeline.reference_resolver import resolve_single_reference

CASES = Path(__file__).parent / "resolution_cases.csv"


def _load_cases() -> list[dict[str, str]]:
    with CASES.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.mark.parametrize("row", _load_cases(), ids=lambda r: r["name"])
def test_resolution_case(row: dict[str, str]) -> None:
    resolved = resolve_single_reference(
        Reference(text=row["reference"].strip(), kind="product_group")
    )
    assert resolved.match_kind == row["match_kind"].strip(), resolved

    scope_dimension = row["scope_dimension"].strip()
    if scope_dimension:
        assert resolved.scope_dimension == scope_dimension, resolved

    scope_value = row["scope_value"].strip()
    if scope_value:
        assert resolved.scope_value == scope_value, resolved

    if row["forbid_name_tokens"].strip() == "1":
        assert not resolved.name_tokens, resolved

    min_raw = row["min_sku_count"].strip()
    if min_raw:
        assert resolved.sku_count >= int(min_raw), resolved
