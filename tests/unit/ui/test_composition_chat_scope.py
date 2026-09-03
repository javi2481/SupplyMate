"""Tests for compact scope labels and commit chat unfreeze policy."""

from __future__ import annotations

from app.core.models import AnalyticalScope
from ui.composition.chat_policy import chat_would_unfreeze
from ui.composition.scope_label import compact_scope_parts, sku_count_caption


def test_chat_would_unfreeze_only_commit_plus_list_explore():
    assert chat_would_unfreeze("commit", "explore") is True
    assert chat_would_unfreeze("commit", "list") is True
    assert chat_would_unfreeze("explore", "explore") is False
    assert chat_would_unfreeze("commit", "single") is False
    assert chat_would_unfreeze("commit", "disambiguation") is False


def test_compact_scope_drops_inventory_root():
    scope = AnalyticalScope(categories=["Pañales"], name_tokens=["xxg"])
    assert compact_scope_parts(scope) == ["Pañales", "XXG"]
    assert sku_count_caption(441, 38) == "441 → 38 SKUs"


def test_empty_scope_is_inventario():
    assert compact_scope_parts(AnalyticalScope()) == ["Inventario"]
