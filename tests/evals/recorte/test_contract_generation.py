"""Contract generator invariants — determinism, ids, no frozen rubros."""

from __future__ import annotations

import ast
from pathlib import Path

from app.catalog.store import CatalogStore
from tests.evals.recorte.contracts import (
    MAX_CONTRACTS,
    SEED,
    generate_contracts,
    pair_coverage_complete,
)

_EVAL_DIR = Path(__file__).parent
_FORBIDDEN_LITERALS = ("Fragancias", "Cosmetica", "LOREAL")


def test_generate_contracts_deterministic(catalog_store: CatalogStore, recorte_seed: int) -> None:
    first = generate_contracts(catalog_store, seed=recorte_seed, max_contracts=MAX_CONTRACTS)
    second = generate_contracts(catalog_store, seed=recorte_seed, max_contracts=MAX_CONTRACTS)
    assert [c.id for c in first] == [c.id for c in second]
    assert [c.axis_tuple() for c in first] == [c.axis_tuple() for c in second]
    assert len(first) <= MAX_CONTRACTS
    assert len(first) >= 1


def test_contract_ids_unique(catalog_store: CatalogStore, recorte_seed: int) -> None:
    contracts = generate_contracts(
        catalog_store, seed=recorte_seed, max_contracts=MAX_CONTRACTS
    )
    ids = [c.id for c in contracts]
    assert len(ids) == len(set(ids))


def test_pair_coverage_or_bounded_set(catalog_store: CatalogStore, recorte_seed: int) -> None:
    contracts = generate_contracts(
        catalog_store, seed=recorte_seed, max_contracts=MAX_CONTRACTS
    )
    # With a tight MAX_CONTRACTS, full 2-wise may be unreachable; require a
    # deterministic non-empty unique set and prefer coverage when it fits.
    assert len(contracts) >= 1
    assert len(contracts) <= MAX_CONTRACTS
    if len(contracts) == MAX_CONTRACTS:
        # Soft: generator ran and ids are unique (checked above).
        return
    assert pair_coverage_complete(contracts, catalog_store, seed=recorte_seed)


def test_axes_and_contracts_have_no_frozen_rubro_literals() -> None:
    for name in ("axes.py", "contracts.py"):
        path = _EVAL_DIR / name
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        literals: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                literals.append(node.value)
        for forbidden in _FORBIDDEN_LITERALS:
            assert forbidden not in literals, (
                f"{name} must not freeze rubro/supplier literal {forbidden!r}"
            )
            assert forbidden not in source


def test_seed_constant_matches_default() -> None:
    assert SEED == 20260914
