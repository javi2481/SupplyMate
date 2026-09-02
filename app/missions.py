"""Mission graph: small curated complement edges (no external graph DB)."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.models import AnalyticalScope
from app.reference_resolver import normalize_text

_MISSIONS_PATH = Path(__file__).resolve().parents[1] / "data" / "missions.csv"


@dataclass(frozen=True)
class MissionEdge:
    from_group: str
    from_dimension: str
    to_group: str
    to_dimension: str
    mission: str
    reason: str
    label: str


@lru_cache(maxsize=1)
def load_missions() -> tuple[MissionEdge, ...]:
    edges: list[MissionEdge] = []
    if not _MISSIONS_PATH.is_file():
        return tuple(edges)
    with _MISSIONS_PATH.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            edges.append(
                MissionEdge(
                    from_group=(row.get("from_group") or "").strip(),
                    from_dimension=(row.get("from_dimension") or "").strip(),
                    to_group=(row.get("to_group") or "").strip(),
                    to_dimension=(row.get("to_dimension") or "").strip(),
                    mission=(row.get("mission") or "").strip(),
                    reason=(row.get("reason") or "").strip(),
                    label=(row.get("label") or "").strip(),
                )
            )
    return tuple(edges)


def _scope_has_group(scope: AnalyticalScope, dimension: str, value: str) -> bool:
    if dimension == "category":
        return value in scope.categories
    if dimension == "subcategory":
        return value in scope.subcategories
    if dimension == "name_token":
        return value in scope.name_tokens
    return False


def mission_neighbors(scope: AnalyticalScope) -> list[MissionEdge]:
    """Complement destinations allowed from the current stable scope."""
    out: list[MissionEdge] = []
    for edge in load_missions():
        if not _scope_has_group(scope, edge.from_dimension, edge.from_group):
            continue
        if _scope_has_group(scope, edge.to_dimension, edge.to_group):
            continue
        out.append(edge)
    return out


def is_complement_target(
    scope: AnalyticalScope,
    *,
    dimension: str,
    value: str,
) -> bool:
    """True when adding this group unions a mission neighbor instead of replacing."""
    for edge in load_missions():
        if edge.to_dimension != dimension or edge.to_group != value:
            continue
        if _scope_has_group(scope, edge.from_dimension, edge.from_group):
            return True
    if dimension == "name_token":
        token = normalize_text(value)
        for edge in load_missions():
            if edge.to_dimension != "name_token":
                continue
            if normalize_text(edge.to_group) != token:
                continue
            if _scope_has_group(scope, edge.from_dimension, edge.from_group):
                return True
    return False


def classify_cut_kind(
    scope: AnalyticalScope | None,
    *,
    dimension: str,
    value: str,
    relation: str,
) -> str:
    """Return and | or | new_query for a resolved group target."""
    if relation != "refinement" or scope is None:
        return "new_query"
    if dimension == "subcategory" and value in scope.subcategories:
        return "and"
    if dimension == "category" and value in scope.categories:
        return "and"
    if dimension == "name_token" and value in scope.name_tokens:
        return "and"
    if is_complement_target(scope, dimension=dimension, value=value):
        return "or"
    if dimension == "category" and value not in scope.categories:
        return "new_query"
    if dimension == "subcategory" and value not in scope.subcategories:
        if scope.categories or scope.subcategories:
            return "new_query"
    return "and"
