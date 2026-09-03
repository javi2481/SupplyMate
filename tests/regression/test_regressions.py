from unittest.mock import AsyncMock, patch

import pytest

from app.agent import run_supplymate
from app.core.models import ChatResponse, DashboardInsight, Reference
from app.pipeline.reference_resolver import resolve_single_reference
from app.services import catalog_service, insight_validator
from tests.catalog_ids import SKU_HIGH_QTY


def test_regression_xxg_does_not_match_xxxg():
    resolved = resolve_single_reference(Reference(text="xxg"))
    assert resolved.match_kind == "group"
    assert "xxg" in resolved.name_tokens
    from app.catalog.store import get_store

    store = get_store()
    for pid in resolved.sku_ids:
        parts = set(store.get_master(pid).product_name.lower().split())
        assert "xxg" in parts
        assert "xxxg" not in parts


def test_regression_insight_rejects_orphan_integer():
    slice_data = catalog_service.replenishment_slice(limit=5)
    if not slice_data.purchase_list:
        pytest.skip("empty purchase list")
    insight = DashboardInsight(
        panel_title="T",
        summary="El recorte mejora un 999 por magia",
        bullets=[],
    )
    errors = insight_validator.validate_insight(insight, slice_data)
    assert any("orphan integer 999" in e for e in errors)


@pytest.mark.asyncio
async def test_regression_chat_qty_from_calculation_not_llm_text():
    expected = catalog_service.get_replenishment_recommendation(SKU_HIGH_QTY)

    async def fake_runner(agent, message, context=None, **kwargs):
        class Result:
            final_output = "Recomiendo pedir 999 unidades inventadas."

        return Result()

    with patch("app.agent.runner.Runner.run", new=AsyncMock(side_effect=fake_runner)):
        response = await run_supplymate(f"¿Cuánto debería pedir de {SKU_HIGH_QTY}?")

    assert isinstance(response, ChatResponse)
    assert response.recommended_quantity == expected.recommended_quantity
    assert response.recommended_quantity != 999
