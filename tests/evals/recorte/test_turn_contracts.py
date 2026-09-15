"""Turn-depth contracts — slice oracle over a bounded purchase set (no LLM)."""

from __future__ import annotations

import pytest

from app.catalog.store import CatalogStore
from app.core.models import AnalyticalScope
from app.core.replenishment import HORIZON_DAYS, clamp_horizon_days
from tests.evals.recorte.contracts import MAX_CONTRACTS, Contract, generate_contracts
from tests.evals.recorte.oracle import (
    assert_emptiness_equivalence,
    assert_no_draft_oc_when_empty,
    assert_slice_matches_filter,
    is_coverage_bucket,
    is_health_bucket,
)
from tests.evals.recorte.pipeline import run_slice

_TURN_LIMIT = 15


def _scope_from_contract(contract: Contract) -> AnalyticalScope:
    """Build category∩subcategory or category∩health from axes (no NL)."""
    horizon = (
        clamp_horizon_days(contract.horizon)
        if contract.horizon is not None
        else HORIZON_DAYS
    )
    tax = contract.taxonomy
    if tax.kind == "subcategory":
        return AnalyticalScope(
            categories=[tax.parent_category] if tax.parent_category else [],
            subcategories=[tax.value],
            horizon_days=horizon,
        )
    scope = AnalyticalScope(categories=[tax.value], horizon_days=horizon)
    if is_health_bucket(contract.risk):
        scope.health_buckets = [contract.risk]
    elif is_coverage_bucket(contract.risk):
        scope.coverage_buckets = [contract.risk]
    return scope


def _turn_contracts(store: CatalogStore, seed: int) -> list[Contract]:
    all_contracts = generate_contracts(store, seed=seed, max_contracts=MAX_CONTRACTS)
    purchase = [c for c in all_contracts if c.route_family == "purchase"]
    # Prefer variety: unique taxonomy keys first.
    seen: set[str] = set()
    chosen: list[Contract] = []
    for contract in purchase:
        key = contract.taxonomy.key()
        if key in seen:
            continue
        seen.add(key)
        chosen.append(contract)
        if len(chosen) >= _TURN_LIMIT:
            break
    if len(chosen) < _TURN_LIMIT:
        for contract in purchase:
            if contract in chosen:
                continue
            chosen.append(contract)
            if len(chosen) >= _TURN_LIMIT:
                break
    return chosen[:_TURN_LIMIT]


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "turn_contract" not in metafunc.fixturenames:
        return
    seed = int(metafunc.config.getoption("--recorte-seed"))
    from app.catalog.store import get_store

    contracts = _turn_contracts(get_store(), seed)
    metafunc.parametrize(
        "turn_contract",
        contracts,
        ids=[c.id for c in contracts],
    )


def test_turn_slice_oracle(turn_contract: Contract) -> None:
    scope = _scope_from_contract(turn_contract)
    slice_data = run_slice(scope, limit=25)
    assert_slice_matches_filter(scope, slice_data)
    assert_emptiness_equivalence(slice_data)
    assert_no_draft_oc_when_empty(slice_data)
    assert slice_data.scope.categories == scope.categories
    assert slice_data.scope.subcategories == scope.subcategories
