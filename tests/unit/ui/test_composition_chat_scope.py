"""Tests for compact scope labels and commit chat unfreeze policy."""

from __future__ import annotations

from app.core.models import AnalyticalScope
from ui.composition.chat_policy import (
    chat_would_unfreeze,
    hide_history_message,
    is_transport_error_message,
    live_dashboard_index,
    should_skip_repeat_purchase_query,
)
from ui.composition.scope_label import compact_scope_parts, sku_count_caption


def test_chat_would_unfreeze_only_commit_plus_list_explore():
    assert chat_would_unfreeze("commit", "explore") is True
    assert chat_would_unfreeze("commit", "list") is True
    assert chat_would_unfreeze("explore", "explore") is False
    assert chat_would_unfreeze("commit", "single") is False
    assert chat_would_unfreeze("commit", "disambiguation") is False


def test_transport_error_and_repeat_purchase_query_are_hidden():
    assert is_transport_error_message("Error 500: Internal Server Error")
    assert should_skip_repeat_purchase_query(
        live=True, prompt="que productos tengo que comprar?"
    )
    assert not should_skip_repeat_purchase_query(
        live=False, prompt="que productos tengo que comprar?"
    )
    messages = [
        {"role": "user", "content": "¿Qué productos tengo que comprar?"},
        {"role": "assistant", "mode": "list", "content": "listo"},
        {"role": "user", "content": "que productos tengo que comprar?"},
        {"role": "assistant", "mode": "error", "content": "Error 500: Internal Server Error"},
    ]
    assert live_dashboard_index(messages, live=True) == 1
    assert not hide_history_message(messages, 0, live=True)
    assert not hide_history_message(messages, 1, live=True)
    assert hide_history_message(messages, 2, live=True)
    assert hide_history_message(messages, 3, live=True)


def test_live_history_keeps_only_latest_explore_turn():
    messages = [
        {"role": "user", "content": "¿Qué productos tengo que comprar?"},
        {
            "role": "assistant",
            "mode": "list",
            "content": "4022 productos en riesgo de quiebre · 25 productos para reponer. Cobertura promedio: 31.6 días.",
        },
        {
            "role": "assistant",
            "mode": "list",
            "content": "4042 en riesgo de quiebre · 25 para reponer",
        },
    ]
    assert live_dashboard_index(messages, live=True) == 2
    assert hide_history_message(messages, 1, live=True)
    assert not hide_history_message(messages, 2, live=True)


def test_compact_scope_drops_inventory_root():
    scope = AnalyticalScope(categories=["Pañales"], name_tokens=["xxg"])
    assert compact_scope_parts(scope) == ["Pañales", "XXG"]
    assert sku_count_caption(441, 38) == "441 → 38 SKUs"


def test_empty_scope_is_inventario():
    assert compact_scope_parts(AnalyticalScope()) == ["Inventario"]
