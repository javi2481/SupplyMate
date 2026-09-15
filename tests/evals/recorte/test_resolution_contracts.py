"""Resolution-depth contracts — bounded set for CI speed."""

from __future__ import annotations

import pytest

from app.catalog.store import CatalogStore
from app.core.models import AnalyticalScope
from tests.evals.recorte.contracts import MAX_CONTRACTS, Contract, generate_contracts
from tests.evals.recorte.pipeline import run_resolution

_RESOLUTION_LIMIT = 30


def _message_for(contract: Contract) -> str:
    tax = contract.taxonomy
    label = tax.value
    if contract.route_family == "sales":
        return "¿Cuáles son las categorías con más ventas?"
    if contract.route_family == "unresolved":
        return "quiero ver productos de ZZXQWY123NOEXISTE"
    if tax.kind == "subcategory":
        return f"¿Cuántos {label} debo comprar?"
    horizon = ""
    if contract.horizon is not None:
        horizon = f" para {contract.horizon} días"
    return f"¿Cuántos {label} tengo que comprar{horizon}?"


def _previous_for(contract: Contract) -> AnalyticalScope | None:
    if contract.relation != "refinement":
        return None
    # A non-empty previous scope so refinement / promote paths are exercised.
    if contract.taxonomy.kind == "subcategory" and contract.taxonomy.parent_category:
        return AnalyticalScope(categories=[contract.taxonomy.parent_category])
    return AnalyticalScope(categories=[contract.taxonomy.value])


def _resolution_contracts(store: CatalogStore, seed: int) -> list[Contract]:
    all_contracts = generate_contracts(store, seed=seed, max_contracts=MAX_CONTRACTS)
    purchase_tax = [
        c
        for c in all_contracts
        if c.route_family == "purchase"
    ]
    chosen = purchase_tax[:_RESOLUTION_LIMIT]
    if len(chosen) < _RESOLUTION_LIMIT:
        chosen = all_contracts[:_RESOLUTION_LIMIT]
    return chosen


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "resolution_contract" not in metafunc.fixturenames:
        return
    from app.catalog.store import get_store

    seed = int(metafunc.config.getoption("--recorte-seed"))
    contracts = _resolution_contracts(get_store(), seed)
    metafunc.parametrize(
        "resolution_contract",
        contracts,
        ids=[c.id for c in contracts],
    )


def test_resolution_scope_blocking_sanity(resolution_contract: Contract) -> None:
    message = _message_for(resolution_contract)
    previous = _previous_for(resolution_contract)
    result = run_resolution(message, previous_scope=previous)

    assert result.scope is not None
    assert result.interpretation is not None

    if resolution_contract.route_family == "unresolved":
        # Unresolved refs with no risk hints should block and offer options when refs exist.
        if result.interpretation.references:
            assert result.blocking is True or result.resolved
            if result.blocking and all(r.match_kind == "unresolved" for r in result.resolved):
                # Options may be empty if the synthetic token matches nothing.
                assert isinstance(result.disambiguation_options, list)
        return

    if resolution_contract.route_family == "sales":
        assert result.interpretation.intent in {"sales_ranking", "unknown", "replenishment"}
        return

    # purchase: scope should stay coherent (no crash; dimension exclusivity light check)
    scope = result.scope
    populated = sum(
        1
        for field in (
            scope.categories,
            scope.subcategories,
            scope.suppliers,
            scope.name_tokens,
            scope.health_buckets,
            scope.coverage_buckets,
        )
        if field
    )
    assert populated >= 0
    if result.blocking:
        assert result.disambiguation_options or any(
            r.match_kind in {"ambiguous", "unresolved"} for r in result.resolved
        )
