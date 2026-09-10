"""Plain-text purchase report for explore chat answers."""

from __future__ import annotations

from app.agent.explore_answer import format_disambiguation_answer, format_explore_answer
from app.core.models import (
    AnalyticalScope,
    ChatInterpretation,
    GroupSummary,
    GuidanceDecision,
    InventoryDashboard,
    PurchaseListItem,
    ReplenishmentSlice,
)


def _item(**kwargs) -> PurchaseListItem:
    base = dict(
        product_id="1",
        product_name="Prod A",
        recommended_quantity=20,
    )
    base.update(kwargs)
    return PurchaseListItem(**base)


def _slice(items: list[PurchaseListItem], *, skus: int = 10, units: int | None = None) -> ReplenishmentSlice:
    total = units if units is not None else sum(i.recommended_quantity for i in items)
    return ReplenishmentSlice(
        scope=AnalyticalScope(categories=["Desodorantes Corporales"]),
        evidence="",
        dashboard=InventoryDashboard(
            skus=skus,
            recommended_units=total,
            purchase_skus=len(items),
        ),
        purchase_list=items,
    )


def test_explore_answer_is_plain_purchase_report():
    items = [
        _item(product_id=str(i), product_name=f"SKU {i}", recommended_quantity=100 - i)
        for i in range(1, 10)
    ]
    text = format_explore_answer(
        _slice(items, skus=409, units=6915),
        ChatInterpretation(
            understood_labels=["Desodorantes Corporales"],
            guidance_question="Para no mezclar grupos, ¿cuál querés analizar primero?",
            guidance_options=["Aerosol", "Roll-on", "Barra"],
        ),
        [GroupSummary(label="Desodorantes Corporales", recommended_quantity=6915, sku_count=409)],
        GuidanceDecision(
            action="ask_clarification",
            question="¿cuál querés analizar primero?",
            options=["Aerosol", "Roll-on"],
            progress_label="Desodorantes Corporales",
            progress_step=1,
            progress_total=4,
        ),
    )

    assert "Entendí" not in text
    assert "Paso" not in text
    assert "**" not in text
    assert "SKU 1" in text
    assert "99 unidades" in text
    assert "Aerosol" not in text
    assert "Roll-on" not in text
    assert "6915" in text
    assert "409" in text


def test_explore_answer_caps_top_eight_skus():
    items = [
        _item(product_id=str(i), product_name=f"SKU {i}", recommended_quantity=50 - i)
        for i in range(1, 12)
    ]
    text = format_explore_answer(
        _slice(items),
        ChatInterpretation(understood_labels=["Cabello"]),
        [],
    )
    assert "SKU 1" in text
    assert "SKU 8" in text
    assert "SKU 9" not in text


def test_explore_answer_empty_slice_plain():
    text = format_explore_answer(
        _slice([]),
        ChatInterpretation(understood_labels=["X"]),
        [],
    )
    assert "**" not in text
    assert "no hay productos" in text.lower()


def test_disambiguation_answer_plain():
    text = format_disambiguation_answer(
        'No estoy seguro de a qué te referís con «cuidado».',
        ["Cuidado del Cabello", "Cuidado de la Piel"],
    )
    assert "**" not in text
    assert "Cuidado del Cabello" in text
