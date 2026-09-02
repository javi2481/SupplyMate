"""Shared size-token helpers for guidance (no imports from guidance.py)."""

from __future__ import annotations

from collections import Counter

from app.reference_resolver import normalize_text
from app.store import get_store

SIZE_RE = r"^x{1,3}g$"
GUIDE_SKU_THRESHOLD = 12


def size_tokens_from_skus(sku_ids: list[str]) -> list[str]:
    import re

    store = get_store()
    counts: Counter[str] = Counter()
    size_re = re.compile(SIZE_RE)
    for pid in sku_ids:
        try:
            master = store.get_master(pid)
        except Exception:
            continue
        for tok in normalize_text(master.product_name).split():
            if size_re.fullmatch(tok):
                counts[tok] += 1
    return [token for token, n in counts.most_common() if n >= 2][:5]
