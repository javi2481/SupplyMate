"""Live-catalog axis enumeration for combinatorial recorte contracts.

Every value is derived from CatalogStore at test time. No rubro, supplier,
or SKU string is frozen in this module.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from app.catalog.store import CatalogStore
from app.services.analytics import metrics
from app.services.analytics.dashboard import COVERAGE_ORDER

_TOKEN_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+")
_MIN_TOKEN_LEN = 3
_MIN_SKUS = 2
_MAX_SUPPLIERS = 15
_MAX_TAXONOMY = 8
_MAX_NAME_TOKENS = 8


@dataclass(frozen=True)
class TaxonomyAxis:
    """A category or subcategory label with enough SKUs to be meaningful."""

    kind: str  # "category" | "subcategory"
    value: str
    parent_category: str = ""

    def key(self) -> str:
        if self.kind == "subcategory" and self.parent_category:
            return f"sub:{self.parent_category}/{self.value}"
        return f"{self.kind}:{self.value}"


@dataclass(frozen=True)
class AxisSet:
    taxonomy: tuple[TaxonomyAxis, ...]
    suppliers: tuple[str, ...]
    risk: tuple[str, ...]
    name_tokens: tuple[str, ...]
    horizons: tuple[int | None, ...]
    relations: tuple[str, ...]
    route_families: tuple[str, ...]

    def as_dict(self) -> dict[str, tuple[Any, ...]]:
        return {
            "taxonomy": self.taxonomy,
            "supplier": self.suppliers,
            "risk": self.risk,
            "name_token": self.name_tokens,
            "horizon": self.horizons,
            "relation": self.relations,
            "route_family": self.route_families,
        }


def _risk_values() -> tuple[str, ...]:
    health = (
        metrics.BUCKET_STOCKOUT_RISK,
        metrics.BUCKET_UNDERSTOCK,
        metrics.BUCKET_OVERSTOCK,
        metrics.BUCKET_HEALTHY,
    )
    return health + tuple(COVERAGE_ORDER)


def enumerate_taxonomy(store: CatalogStore) -> tuple[TaxonomyAxis, ...]:
    """Categories/subcategories with ≥2 SKUs; prefer cats that have ≥2 subs."""
    by_cat: dict[str, list] = defaultdict(list)
    by_sub: dict[tuple[str, str], list] = defaultdict(list)
    for master in store.products.values():
        cat = (master.category or "").strip()
        sub = (master.subcategory or "").strip()
        if cat:
            by_cat[cat].append(master)
        if cat and sub:
            by_sub[(cat, sub)].append(master)

    cats_with_skus = {c: ms for c, ms in by_cat.items() if len(ms) >= _MIN_SKUS}
    subs_with_skus = {
        (c, s): ms for (c, s), ms in by_sub.items() if len(ms) >= _MIN_SKUS
    }

    subs_per_cat: dict[str, set[str]] = defaultdict(set)
    for cat, sub in subs_with_skus:
        subs_per_cat[cat].add(sub)

    preferred_cats = sorted(
        (c for c, subs in subs_per_cat.items() if len(subs) >= 2 and c in cats_with_skus),
        key=lambda c: (-len(subs_per_cat[c]), -len(cats_with_skus[c]), c),
    )
    other_cats = sorted(
        (c for c in cats_with_skus if c not in preferred_cats),
        key=lambda c: (-len(cats_with_skus[c]), c),
    )
    ordered_cats = preferred_cats + other_cats

    selected: list[TaxonomyAxis] = []
    for cat in ordered_cats:
        if len(selected) >= _MAX_TAXONOMY:
            break
        selected.append(TaxonomyAxis(kind="category", value=cat))
        for sub in sorted(subs_per_cat.get(cat, ())):
            if len(selected) >= _MAX_TAXONOMY:
                break
            if (cat, sub) in subs_with_skus:
                selected.append(
                    TaxonomyAxis(kind="subcategory", value=sub, parent_category=cat)
                )
    return tuple(selected)


def enumerate_suppliers(store: CatalogStore, *, limit: int = _MAX_SUPPLIERS) -> tuple[str, ...]:
    counts: Counter[str] = Counter()
    for master in store.products.values():
        supplier = (master.supplier or "").strip()
        if supplier:
            counts[supplier] += 1
    eligible = sorted(
        (name for name, n in counts.items() if n >= _MIN_SKUS),
        key=lambda name: (-counts[name], name),
    )
    return tuple(eligible[:limit])


def enumerate_name_tokens(
    store: CatalogStore,
    *,
    limit: int = _MAX_NAME_TOKENS,
) -> tuple[str, ...]:
    """Tokens appearing in ≥2 product names; skip short tokens (<3 chars)."""
    token_counts: Counter[str] = Counter()
    token_categories: dict[str, set[str]] = defaultdict(set)
    for master in store.products.values():
        name = master.product_name or ""
        cat = (master.category or "").strip()
        seen_in_name: set[str] = set()
        for raw in _TOKEN_RE.findall(name):
            token = raw.lower()
            if len(token) < _MIN_TOKEN_LEN:
                continue
            if token in seen_in_name:
                continue
            seen_in_name.add(token)
            token_counts[token] += 1
            if cat:
                token_categories[token].add(cat)

    # Prefer tokens with enough hits and contained by few categories (family-shaped).
    candidates = [
        tok
        for tok, n in token_counts.items()
        if n >= _MIN_SKUS and len(token_categories.get(tok, ())) <= 3
    ]
    candidates.sort(
        key=lambda tok: (
            len(token_categories.get(tok, ())),
            -token_counts[tok],
            tok,
        )
    )
    return tuple(candidates[:limit])


def enumerate_axes(store: CatalogStore) -> AxisSet:
    return AxisSet(
        taxonomy=enumerate_taxonomy(store),
        suppliers=enumerate_suppliers(store),
        risk=_risk_values(),
        name_tokens=enumerate_name_tokens(store),
        horizons=(None, 15, 30),
        relations=("new_query", "refinement"),
        route_families=("purchase", "sales", "unresolved"),
    )


def catalog_shape(store: CatalogStore) -> dict[str, Any]:
    """Coarse shape snapshot — counts bucketed to the nearest 10 %, no node labels."""
    cats: set[str] = set()
    subs: set[str] = set()
    suppliers: set[str] = set()
    for master in store.products.values():
        if master.category:
            cats.add(master.category.strip())
        if master.subcategory:
            subs.add(master.subcategory.strip())
        if master.supplier:
            suppliers.add(master.supplier.strip())
    return {
        "n_categories": bucket_nearest_10pct(len(cats)),
        "n_subcategories": bucket_nearest_10pct(len(subs)),
        "n_suppliers": bucket_nearest_10pct(len(suppliers)),
        "n_skus_bucketed": bucket_nearest_10pct(len(store.products)),
        "coverage_order": list(COVERAGE_ORDER),
        "health_buckets": list(_risk_values()[:4]),
    }


def bucket_nearest_10pct(n: int) -> int:
    if n <= 0:
        return 0
    step = max(1, int(round(n * 0.1)))
    return int(round(n / step) * step)


def live_counts(store: CatalogStore) -> dict[str, int]:
    cats: set[str] = set()
    subs: set[str] = set()
    suppliers: set[str] = set()
    for master in store.products.values():
        if master.category:
            cats.add(master.category.strip())
        if master.subcategory:
            subs.add(master.subcategory.strip())
        if master.supplier:
            suppliers.add(master.supplier.strip())
    return {
        "n_categories": len(cats),
        "n_subcategories": len(subs),
        "n_suppliers": len(suppliers),
        "n_skus_bucketed": len(store.products),
    }
