"""Guard: legacy golden CSVs are frozen in row count; add new cases under traps/ or eval contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

GOLDEN_ROOT = Path(__file__).parent

FROZEN_COUNTS: dict[str, int] = {
    "intents/golden_intents.csv": 35,
    "multiturn/golden_multiturn.csv": 4,
    "query_interpretation/golden_query_interpretation.csv": 10,
    "reference_resolution/golden_reference_resolution.csv": 16,
}

POINTER = (
    "Add new regression strings to tests/golden/traps/traps.csv "
    "or a generated recorte contract — do not grow the legacy golden CSVs."
)


def _line_count(path: Path) -> int:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return sum(1 for _ in fh)


@pytest.mark.parametrize("relative,frozen", sorted(FROZEN_COUNTS.items()))
def test_golden_csv_row_count_is_frozen(relative: str, frozen: int) -> None:
    path = GOLDEN_ROOT / relative
    assert path.is_file(), f"missing golden fixture {relative}"
    got = _line_count(path)
    assert got == frozen, f"{relative}: expected {frozen} lines (incl. header), got {got}. {POINTER}"
