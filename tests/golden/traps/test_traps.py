"""Known regression traps — oracle predicates only, never answer-text goldens."""

from __future__ import annotations

import csv
import re
from pathlib import Path

import pytest

from app.agent.explore_answer import format_explore_answer
from app.core.models import (
    AnalyticalScope,
    ChatInterpretation,
    GroupSummary,
    GuidanceDecision,
    InventoryDashboard,
    Reference,
    ReplenishmentSlice,
)
from app.catalog.store import get_store
from app.pipeline.reference_resolver import resolve_single_reference

TRAPS = Path(__file__).parent / "traps.csv"

_CLAIM_RE = re.compile(r"\d+\s*(?:unidades|u\.)|\d+\s*SKUs\s*a\s+reponer", re.IGNORECASE)


def _load_traps() -> list[dict[str, str]]:
    with TRAPS.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _replenishment_claims(text: str) -> list[str]:
    return _CLAIM_RE.findall(text)


def _assert_unresolved_supplier(message: str, _previous_scope: str) -> None:
    resolved = resolve_single_reference(Reference(text=message, kind="product_group"))
    assert resolved.match_kind == "unresolved", resolved
    assert not resolved.sku_ids


def _assert_size_token_not_xxxg(message: str, _previous_scope: str) -> None:
    resolved = resolve_single_reference(Reference(text=message))
    assert resolved.match_kind == "group", resolved
    assert message.lower() in resolved.name_tokens
    store = get_store()
    for pid in resolved.sku_ids:
        parts = set(store.get_master(pid).product_name.lower().split())
        assert message.lower() in parts
        assert "xxxg" not in parts


def _assert_empty_purchase_no_claim(_message: str, _previous_scope: str) -> None:
    slice_data = ReplenishmentSlice(
        scope=AnalyticalScope(categories=["Desodorantes Corporales"]),
        evidence="",
        dashboard=InventoryDashboard(
            skus=120,
            recommended_units=4200,
            purchase_skus=37,
        ),
        purchase_list=[],
    )
    text = format_explore_answer(
        slice_data,
        ChatInterpretation(understood_labels=["Grupo A"]),
        [GroupSummary(label="Grupo A", recommended_quantity=4200, sku_count=37)],
        GuidanceDecision(
            action="draft_oc",
            question="Con este recorte hay 0 líneas a reponer (0 u.). ¿Armamos la OC?",
            options=["Armar OC"],
        ),
    )
    assert _replenishment_claims(text) == []
    assert "Armamos la OC" not in text
    assert "no hay productos" in text.lower()


def _assert_toallitas_name_hit_set(message: str, _previous_scope: str) -> None:
    resolved = resolve_single_reference(Reference(text=message, kind="product_group"))
    assert resolved.match_kind == "group", resolved
    assert resolved.scope_dimension == "sku_set", resolved
    assert message.lower() in resolved.name_tokens
    assert len(resolved.sku_ids) >= 2


ASSERTIONS = {
    "unresolved_supplier": _assert_unresolved_supplier,
    "size_token_not_xxxg": _assert_size_token_not_xxxg,
    "empty_purchase_no_claim": _assert_empty_purchase_no_claim,
    "toallitas_name_hit_set": _assert_toallitas_name_hit_set,
}


@pytest.mark.parametrize("row", _load_traps(), ids=lambda r: r["name"])
def test_trap_oracle(row: dict[str, str]) -> None:
    assertion = row["assertion"].strip()
    handler = ASSERTIONS.get(assertion)
    assert handler is not None, f"unknown trap assertion {assertion!r}"
    handler(row["message"].strip(), row["previous_scope"].strip())
