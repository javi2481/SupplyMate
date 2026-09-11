"""Plain-text purchase report for explore chat answers."""

from __future__ import annotations

from app.agent.explore_answer import format_explore_answer
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


def _slice(
    items: list[PurchaseListItem],
    *,
    skus: int = 10,
    units: int | None = None,
    purchase_skus: int | None = None,
) -> ReplenishmentSlice:
    total = units if units is not None else sum(i.recommended_quantity for i in items)
    return ReplenishmentSlice(
        scope=AnalyticalScope(categories=["Desodorantes Corporales"]),
        evidence="",
        dashboard=InventoryDashboard(
            skus=skus,
            recommended_units=total,
            purchase_skus=purchase_skus if purchase_skus is not None else len(items),
        ),
        purchase_list=items,
    )


def test_explore_answer_is_plain_purchase_report():
    items = [
        _item(product_id=str(i), product_name=f"SKU {i}", recommended_quantity=100 - i)
        for i in range(1, 10)
    ]
    text = format_explore_answer(
        _slice(items, skus=409, units=6915, purchase_skus=409),
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


def test_explore_answer_uses_purchase_skus_not_catalog_skus():
    items = [_item(product_id="1", product_name="A", recommended_quantity=50)]
    text = format_explore_answer(
        ReplenishmentSlice(
            scope=AnalyticalScope(
                categories=["Cosmetica"],
                coverage_buckets=["0–3 días"],
                health_buckets=["stockout_risk"],
            ),
            evidence="",
            dashboard=InventoryDashboard(
                skus=500,
                recommended_units=50,
                purchase_skus=12,
            ),
            purchase_list=items,
        ),
        ChatInterpretation(understood_labels=["Cosmetica"]),
        [],
    )
    assert "12 SKUs a reponer" in text
    assert "500" not in text
    assert "0–3 días" in text
    assert "Críticos" in text


def test_format_single_product_uses_calc_horizon():
    from app.services import catalog_service
    from app.services.analytics.catalog_service import format_single_product_answer
    from tests.catalog_ids import SKU_HIGH_QTY

    rec = catalog_service.get_replenishment_recommendation(SKU_HIGH_QTY, horizon_days=14)
    text = format_single_product_answer(rec)
    assert "demanda 14 días" in text
    assert "demanda 7 días" not in text
