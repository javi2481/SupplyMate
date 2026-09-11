"""Plain-text purchase report for explore chat answers."""

from __future__ import annotations

import re

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

_CLAIM_RE = re.compile(r"\d+\s*(?:unidades|u\.)|\d+\s*SKUs\s+a\s+reponer", re.IGNORECASE)
_UNITS_CLAIM_RE = re.compile(r"(\d+)\s+unidades a reponer")
_SKUS_CLAIM_RE = re.compile(r"(\d+)\s+SKUs a reponer")


def _replenishment_claims(text: str) -> list[str]:
    """Every number the answer presents as a quantity to buy.

    Structural probe: the recorte size ("N SKUs · próximos D días") and the panel
    remainder ("y N más en el panel") are not claims and must not be reported here.
    """
    return _CLAIM_RE.findall(text)


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


def test_explore_answer_empty_ignores_group_summaries_and_draft_oc():
    """Intersected scope empty must not invent totals from per-ref summaries."""
    text = format_explore_answer(
        _slice([], skus=0, units=0, purchase_skus=0),
        ChatInterpretation(understood_labels=["UNILEVER", "Cosmetica"]),
        [
            GroupSummary(label="UNILEVER", recommended_quantity=5000, sku_count=200),
            GroupSummary(label="Cosmetica", recommended_quantity=300, sku_count=42),
        ],
        GuidanceDecision(
            action="draft_oc",
            question="Con este recorte hay 0 líneas a reponer (0 u.). ¿Armamos la OC?",
            options=["Armar OC"],
        ),
    )
    assert "5000" not in text
    assert "200" not in text
    assert "242" not in text
    assert "Armamos la OC" not in text
    assert "no hay productos" in text.lower() or "no hay" in text.lower()


def test_explore_answer_empty_purchase_list_makes_no_claim():
    """An empty purchase list is the emptiness fact; dashboard counters cannot override it."""
    text = format_explore_answer(
        _slice([], skus=120, units=4200, purchase_skus=37),
        ChatInterpretation(understood_labels=["Grupo A"]),
        [GroupSummary(label="Grupo A", recommended_quantity=4200, sku_count=37)],
    )
    assert _replenishment_claims(text) == []
    assert "no hay productos" in text.lower()


def test_explore_answer_empty_never_renders_group_summary_totals():
    text = format_explore_answer(
        _slice([], skus=250, units=5042, purchase_skus=242),
        ChatInterpretation(understood_labels=["Grupo A", "Grupo B"]),
        [
            GroupSummary(label="Grupo A", recommended_quantity=5000, sku_count=200),
            GroupSummary(label="Grupo B", recommended_quantity=42, sku_count=42),
        ],
    )
    assert _replenishment_claims(text) == []
    assert "5000" not in text


def test_explore_answer_claims_equal_dashboard_counters():
    items = [
        _item(product_id=str(i), product_name=f"SKU {i}", recommended_quantity=30 - i)
        for i in range(1, 4)
    ]
    text = format_explore_answer(
        _slice(items, skus=310, units=7400, purchase_skus=88),
        ChatInterpretation(understood_labels=["Grupo A"]),
        [GroupSummary(label="Grupo A", recommended_quantity=999, sku_count=999)],
    )
    units_claim = _UNITS_CLAIM_RE.search(text)
    skus_claim = _SKUS_CLAIM_RE.search(text)
    assert units_claim is not None and units_claim.group(1) == "7400"
    assert skus_claim is not None and skus_claim.group(1) == "88"
    # purchase_skus beyond the listed lines is only "how many more are in the panel".
    assert "85 más en el panel" in text
    assert "999" not in text


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
