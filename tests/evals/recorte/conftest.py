"""Session fixtures and options for combinatorial recorte evals."""

from __future__ import annotations

import pytest

from app.catalog.store import CatalogStore, get_store
from tests.evals.recorte.contracts import SEED


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--recorte-seed",
        action="store",
        type=int,
        default=SEED,
        help="Seed for combinatorial recorte contract generation (CI uses the module default).",
    )


@pytest.fixture(scope="session")
def catalog_store() -> CatalogStore:
    """Reuse one CatalogStore across the eval suite (~13k SKUs)."""
    return get_store()


@pytest.fixture(scope="session")
def recorte_seed(pytestconfig: pytest.Config) -> int:
    return int(pytestconfig.getoption("--recorte-seed"))
