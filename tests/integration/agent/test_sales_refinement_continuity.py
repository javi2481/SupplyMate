"""Sales panel replacement must not wipe a prior purchase recorte on refinement.

The eval harness (`tests/evals/recorte/test_turn_contracts.py`) is not built yet,
so this focused two-turn contract stands in for Phase 7 task 7.7.
"""

from __future__ import annotations

from collections import Counter

import pytest

from app.agent import run_supplymate
from app.catalog.store import get_store
from app.core.models import AnalyticalScope, Reference
from app.pipeline.query_interpretation import classify_relation
from app.pipeline.reference_resolver import normalize_text, resolve_single_reference


def _live_group_label() -> str:
    counts: Counter[str] = Counter()
    for product in get_store().products.values():
        if product.category:
            counts[product.category] += 1
    for label, count in counts.most_common():
        if count < 10:
            continue
        token = next((part for part in normalize_text(label).split() if len(part) >= 4), "")
        if not token:
            continue
        resolved = resolve_single_reference(Reference(text=token))
        if resolved.match_kind == "group" and resolved.scope_value:
            return resolved.scope_value
    raise AssertionError("live catalog has no resolvable taxonomy group with ≥10 SKUs")


def _taxonomy_values(scope: AnalyticalScope | None) -> set[str]:
    if scope is None:
        return set()
    return set(scope.categories) | set(scope.subcategories)


@pytest.mark.asyncio
async def test_sales_then_refinement_keeps_prior_purchase_recorte():
    label = _live_group_label()
    first = await run_supplymate(f"¿Cuántos {label} debo comprar?")
    prior = _taxonomy_values(first.scope)
    assert prior, f"purchase turn did not build a recorte for live group {label!r}"

    sales = await run_supplymate("cuales son las categorias mas vendidas", first.scope)
    assert sales.mode == "sales"
    assert sales.dashboard is not None
    assert sales.scope is not None
    assert _taxonomy_values(sales.scope) == set()

    follow = "solo los de riesgo"
    assert classify_relation(follow, first.scope) == "refinement"
    assert classify_relation(follow, sales.scope) == "new_query"

    refined = await run_supplymate(follow, first.scope)
    assert classify_relation(follow, first.scope) == "refinement"
    kept = _taxonomy_values(refined.scope)
    assert prior & kept, (
        "follow-up with the pre-sales recorte as previous must keep that recorte, "
        f"got {kept!r} after {prior!r}"
    )
    assert refined.scope is not None
    assert refined.scope.health_buckets, "refinement should add the risk filter"

    wiped = await run_supplymate(follow, sales.scope)
    assert not (_taxonomy_values(wiped.scope) & prior), (
        "sending the sales root scope as previous would wipe the purchase recorte — "
        "the client must keep conversationSlice, not the replaced panel slice"
    )
