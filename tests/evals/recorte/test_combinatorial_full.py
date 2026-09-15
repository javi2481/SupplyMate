"""Opt-in full cartesian smoke — deselected unless ``-m combinatorial_full``."""

from __future__ import annotations

import pytest

from app.catalog.store import CatalogStore
from tests.evals.recorte.contracts import generate_contracts

pytestmark = pytest.mark.combinatorial_full


def test_full_cartesian_generates(catalog_store: CatalogStore, recorte_seed: int) -> None:
    contracts = generate_contracts(
        catalog_store,
        seed=recorte_seed,
        max_contracts=80,
        full=True,
    )
    assert len(contracts) >= 1
    ids = [c.id for c in contracts]
    assert len(ids) == len(set(ids))
