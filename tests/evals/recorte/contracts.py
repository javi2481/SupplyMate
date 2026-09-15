"""Pairwise contract generation over live catalog axes."""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, field
from typing import Any

from app.catalog.store import CatalogStore
from tests.evals.recorte.axes import AxisSet, TaxonomyAxis, enumerate_axes

SEED = 20260914
MAX_CONTRACTS = 80  # keep CI fast on ~13k catalog


@dataclass(frozen=True)
class ContractExpectations:
    """Relational expectations — never absolute per-node counts."""

    route_family: str
    relation: str
    expect_blocking_if_unresolved: bool = True


@dataclass(frozen=True)
class Contract:
    id: str
    taxonomy: TaxonomyAxis
    supplier: str
    risk: str
    name_token: str
    horizon: int | None
    relation: str
    route_family: str
    expectations: ContractExpectations = field(repr=False)

    def axis_tuple(self) -> tuple[Any, ...]:
        return (
            self.taxonomy.key(),
            self.supplier,
            self.risk,
            self.name_token,
            self.horizon,
            self.relation,
            self.route_family,
        )


def _stable_id(axis_tuple: tuple[Any, ...]) -> str:
    parts = []
    for value in axis_tuple:
        text = "none" if value is None else str(value)
        text = text.replace(" ", "_").replace("/", "-")
        parts.append(text)
    return "|".join(parts)


def _pair_key(axis_a: str, value_a: Any, axis_b: str, value_b: Any) -> tuple:
    return (axis_a, value_a, axis_b, value_b)


def _uncovered_pairs(axes: dict[str, tuple[Any, ...]]) -> set[tuple]:
    uncovered: set[tuple] = set()
    names = list(axes.keys())
    for left, right in itertools.combinations(names, 2):
        for va in axes[left]:
            for vb in axes[right]:
                uncovered.add(_pair_key(left, va, right, vb))
    return uncovered


def _pairs_covered_by(combo: dict[str, Any]) -> set[tuple]:
    covered: set[tuple] = set()
    names = list(combo.keys())
    for left, right in itertools.combinations(names, 2):
        covered.add(_pair_key(left, combo[left], right, combo[right]))
    return covered


def _combo_from_values(
    taxonomy: TaxonomyAxis,
    supplier: str,
    risk: str,
    name_token: str,
    horizon: int | None,
    relation: str,
    route_family: str,
) -> dict[str, Any]:
    return {
        "taxonomy": taxonomy,
        "supplier": supplier,
        "risk": risk,
        "name_token": name_token,
        "horizon": horizon,
        "relation": relation,
        "route_family": route_family,
    }


def _contract_from_combo(combo: dict[str, Any]) -> Contract:
    axis_tuple = (
        combo["taxonomy"].key(),
        combo["supplier"],
        combo["risk"],
        combo["name_token"],
        combo["horizon"],
        combo["relation"],
        combo["route_family"],
    )
    route_family = combo["route_family"]
    relation = combo["relation"]
    return Contract(
        id=_stable_id(axis_tuple),
        taxonomy=combo["taxonomy"],
        supplier=combo["supplier"],
        risk=combo["risk"],
        name_token=combo["name_token"],
        horizon=combo["horizon"],
        relation=relation,
        route_family=route_family,
        expectations=ContractExpectations(
            route_family=route_family,
            relation=relation,
            expect_blocking_if_unresolved=(route_family == "unresolved"),
        ),
    )


def _sample_axis_values(axes: AxisSet, rng: random.Random) -> dict[str, tuple[Any, ...]]:
    """Shrink live enumerations so 2-wise fits under MAX_CONTRACTS."""
    taxonomy = list(axes.taxonomy)
    suppliers = list(axes.suppliers)
    name_tokens = list(axes.name_tokens)
    rng.shuffle(taxonomy)
    rng.shuffle(suppliers)
    rng.shuffle(name_tokens)
    # Keep enough diversity for pairwise without blowing the 80-contract budget.
    return {
        "taxonomy": tuple(taxonomy[:6]),
        "supplier": tuple(suppliers[:6]),
        "risk": axes.risk,
        "name_token": tuple(name_tokens[:6]),
        "horizon": axes.horizons,
        "relation": axes.relations,
        "route_family": axes.route_families,
    }


def _greedy_pairwise(
    values: dict[str, tuple[Any, ...]],
    rng: random.Random,
    *,
    max_contracts: int,
) -> list[dict[str, Any]]:
    """Greedy 2-wise selection over a shuffled candidate stream."""
    uncovered = _uncovered_pairs(values)
    keys = list(values.keys())
    # Materialize a shuffled candidate pool (cartesian can be large — stream samples).
    pool_size = min(5000, max_contracts * 40)
    candidates: list[dict[str, Any]] = []
    for _ in range(pool_size):
        combo = {k: rng.choice(values[k]) for k in keys}
        candidates.append(combo)
    # Also include a systematic slice of the cartesian for stability on small axes.
    product_iter = itertools.product(*(values[k] for k in keys))
    for i, row in enumerate(product_iter):
        if i >= pool_size:
            break
        candidates.append(dict(zip(keys, row)))
    rng.shuffle(candidates)

    selected: list[dict[str, Any]] = []
    seen: set[tuple] = set()
    while uncovered and len(selected) < max_contracts:
        best: dict[str, Any] | None = None
        best_gain = -1
        best_idx = -1
        for idx, combo in enumerate(candidates):
            key = tuple(combo[k] for k in keys)
            if key in seen:
                continue
            gain = len(uncovered & _pairs_covered_by(combo))
            if gain > best_gain:
                best_gain = gain
                best = combo
                best_idx = idx
        if best is None or best_gain <= 0:
            break
        selected.append(best)
        seen.add(tuple(best[k] for k in keys))
        uncovered -= _pairs_covered_by(best)
        # Drop the chosen candidate to keep scans cheap.
        if best_idx >= 0:
            candidates.pop(best_idx)

    if uncovered and len(selected) >= max_contracts:
        # Cap reached before full pair coverage — caller may treat as soft.
        return selected
    return selected


def _full_cartesian(values: dict[str, tuple[Any, ...]]) -> list[dict[str, Any]]:
    keys = list(values.keys())
    return [dict(zip(keys, row)) for row in itertools.product(*(values[k] for k in keys))]


def generate_contracts(
    store: CatalogStore,
    seed: int = SEED,
    max_contracts: int = MAX_CONTRACTS,
    full: bool = False,
) -> list[Contract]:
    """Generate a seeded, capped contract set (or full cartesian when ``full``)."""
    rng = random.Random(seed)
    axis_set = enumerate_axes(store)
    values = _sample_axis_values(axis_set, rng)

    if full:
        combos = _full_cartesian(values)
        # Still bound extreme cartesian blow-ups for safety.
        if len(combos) > max_contracts * 20:
            rng.shuffle(combos)
            combos = combos[: max_contracts * 20]
    else:
        combos = _greedy_pairwise(values, rng, max_contracts=max_contracts)
        if len(combos) > max_contracts:
            raise RuntimeError(
                f"Pairwise selection produced {len(combos)} contracts; "
                f"cap is {max_contracts}. Reduce axis samples or raise MAX_CONTRACTS."
            )

    contracts = [_contract_from_combo(c) for c in combos]
    # Stable order by id for determinism across runs.
    contracts.sort(key=lambda c: c.id)
    if not full and len(contracts) > max_contracts:
        contracts = contracts[:max_contracts]
    return contracts


def pair_coverage_complete(
    contracts: list[Contract],
    store: CatalogStore,
    seed: int = SEED,
) -> bool:
    """Whether the contract set covers every 2-wise pair of the sampled axes."""
    rng = random.Random(seed)
    values = _sample_axis_values(enumerate_axes(store), rng)
    uncovered = _uncovered_pairs(values)
    for contract in contracts:
        combo = _combo_from_values(
            contract.taxonomy,
            contract.supplier,
            contract.risk,
            contract.name_token,
            contract.horizon,
            contract.relation,
            contract.route_family,
        )
        uncovered -= _pairs_covered_by(combo)
    return not uncovered
