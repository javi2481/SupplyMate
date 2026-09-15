"""Catalog shape drift — fail loudly when the live store changes world-shape."""

from __future__ import annotations

import json
from pathlib import Path

from app.catalog.store import CatalogStore
from tests.evals.recorte.axes import (
    bucket_nearest_10pct,
    catalog_shape,
    live_counts,
)

_SNAPSHOT = Path(__file__).parent / "catalog_shape.json"
_REFRESH = (
    "Refresh with: python -c \"from app.catalog.store import get_store; "
    "from tests.evals.recorte.axes import catalog_shape; import json; "
    "print(json.dumps(catalog_shape(get_store()), indent=2, ensure_ascii=False))\""
)


def test_live_store_matches_catalog_shape(catalog_store: CatalogStore) -> None:
    assert _SNAPSHOT.is_file(), (
        f"Missing {_SNAPSHOT.name}. {_REFRESH}"
    )
    expected = json.loads(_SNAPSHOT.read_text(encoding="utf-8"))
    live = catalog_shape(catalog_store)
    raw = live_counts(catalog_store)

    for key in (
        "n_categories",
        "n_subcategories",
        "n_suppliers",
        "n_skus_bucketed",
    ):
        assert key in expected, f"snapshot missing {key}; {_REFRESH}"
        bucketed_live = live[key]
        # Exact bucket match, or raw within ±10% of snapshot bucket.
        snap = expected[key]
        if bucketed_live != snap:
            denom = max(snap, 1)
            rel = abs(raw[key] - snap) / denom
            assert rel <= 0.10 or bucket_nearest_10pct(raw[key]) == snap, (
                f"Catalog shape drifted on {key}: live_raw={raw[key]}, "
                f"live_bucketed={bucketed_live}, snapshot={snap}. {_REFRESH}"
            )

    assert live["coverage_order"] == expected["coverage_order"], (
        f"coverage_order drifted: {live['coverage_order']!r} vs "
        f"{expected['coverage_order']!r}. {_REFRESH}"
    )
    assert live["health_buckets"] == expected["health_buckets"], (
        f"health_buckets drifted: {live['health_buckets']!r} vs "
        f"{expected['health_buckets']!r}. {_REFRESH}"
    )
