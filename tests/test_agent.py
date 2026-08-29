from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.agent import run_supplymate
from app.models import (
    ChatResponse,
    Inventory,
    ProductNotFoundError,
    ReplenishmentParams,
    SaleRecord,
    SalesHistory,
    SupplyContext,
)
from app.replenishment import calculate_replenishment
from app.services import catalog_service
from tests.catalog_ids import SKU_HIGH_QTY, SKU_UNKNOWN, SKU_ZERO_QTY


def _seed_context_for_high_qty() -> SupplyContext:
    rec = catalog_service.get_replenishment_recommendation(SKU_HIGH_QTY)
    ctx = SupplyContext(product_id=SKU_HIGH_QTY)
    ctx.inventory = Inventory(product_id=SKU_HIGH_QTY, current_stock=rec.context.current_stock)
    start = date(2026, 7, 27)
    avg = int(rec.calculation.average_daily_demand)
    ctx.sales = SalesHistory(
        product_id=SKU_HIGH_QTY,
        days=30,
        records=[
            SaleRecord(date=start + timedelta(days=i), units_sold=avg) for i in range(30)
        ],
    )
    ctx.params = ReplenishmentParams(
        product_id=SKU_HIGH_QTY,
        lead_time_days=rec.calculation.lead_time_days,
        safety_stock=rec.calculation.safety_stock,
    )
    return ctx


@pytest.mark.asyncio
async def test_run_supplymate_quantity_matches_python_calc():
    ctx = _seed_context_for_high_qty()
    expected = catalog_service.get_replenishment_recommendation(SKU_HIGH_QTY)

    async def fake_runner(agent, message, context=None, **kwargs):
        class Result:
            final_output = f"Recomiendo pedir {expected.recommended_quantity}."

        if context is not None and hasattr(agent, "tools") and agent.tools:
            context.product_id = ctx.product_id
            context.inventory = ctx.inventory
            context.sales = ctx.sales
            context.params = ctx.params
        return Result()

    with patch("app.agent.Runner.run", new=AsyncMock(side_effect=fake_runner)):
        response = await run_supplymate(f"¿Cuánto debería pedir de {SKU_HIGH_QTY}?")

    assert isinstance(response, ChatResponse)
    assert response.product_id == SKU_HIGH_QTY
    assert response.recommended_quantity == expected.recommended_quantity
    assert response.recommended_quantity == 172


@pytest.mark.asyncio
async def test_run_supplymate_zero_quantity_triangulation():
    rec = catalog_service.get_replenishment_recommendation(SKU_ZERO_QTY)
    ctx = SupplyContext(product_id=SKU_ZERO_QTY)
    ctx.inventory = Inventory(
        product_id=SKU_ZERO_QTY, current_stock=rec.context.current_stock
    )
    start = date(2026, 7, 27)
    avg = int(rec.calculation.average_daily_demand) or 1
    ctx.sales = SalesHistory(
        product_id=SKU_ZERO_QTY,
        days=30,
        records=[
            SaleRecord(date=start + timedelta(days=i), units_sold=avg) for i in range(30)
        ],
    )
    ctx.params = ReplenishmentParams(
        product_id=SKU_ZERO_QTY,
        lead_time_days=rec.calculation.lead_time_days,
        safety_stock=rec.calculation.safety_stock,
    )

    async def fake_runner(agent, message, context=None, **kwargs):
        class Result:
            final_output = "No hace falta pedir."

        if context is not None and hasattr(agent, "tools") and agent.tools:
            context.product_id = ctx.product_id
            context.inventory = ctx.inventory
            context.sales = ctx.sales
            context.params = ctx.params
        return Result()

    with patch("app.agent.Runner.run", new=AsyncMock(side_effect=fake_runner)):
        response = await run_supplymate(f"¿Cuánto pedir de {SKU_ZERO_QTY}?")

    assert response.recommended_quantity == 0
    assert response.product_id == SKU_ZERO_QTY


@pytest.mark.asyncio
async def test_run_supplymate_unknown_product():
    async def fake_runner(agent, message, context=None, **kwargs):
        class Result:
            final_output = "No encontré el producto."

        return Result()

    with patch("app.agent.Runner.run", new=AsyncMock(side_effect=fake_runner)):
        with pytest.raises(ProductNotFoundError):
            await run_supplymate(f"¿Cuánto pedir de {SKU_UNKNOWN}?")


@pytest.mark.asyncio
async def test_run_supplymate_purchase_list():
    response = await run_supplymate("¿Qué productos tengo que comprar?")
    assert response.mode == "list"
    assert response.purchase_list
    assert len(response.purchase_list) <= 25
    assert all(item.recommended_quantity > 0 for item in response.purchase_list)
    assert "productos" in response.answer.lower()


@pytest.mark.asyncio
async def test_fallback_hydrates_when_agent_skips_tools():
    expected = catalog_service.get_replenishment_recommendation(SKU_HIGH_QTY)

    async def fake_runner(agent, message, context=None, **kwargs):
        class Result:
            final_output = f"Recomiendo pedir {expected.recommended_quantity}."

        return Result()

    with patch("app.agent.Runner.run", new=AsyncMock(side_effect=fake_runner)):
        response = await run_supplymate(f"cuanto pedir de {SKU_HIGH_QTY}")

    assert response.product_id == SKU_HIGH_QTY
    assert response.recommended_quantity == expected.recommended_quantity
