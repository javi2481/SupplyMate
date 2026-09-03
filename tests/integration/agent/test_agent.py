from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.agent import run_supplymate
from app.core.models import (
    ChatResponse,
    Inventory,
    ProductNotFoundError,
    ReplenishmentParams,
    SaleRecord,
    SalesHistory,
    SupplyContext,
)
from app.core.replenishment import calculate_replenishment
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

    with patch("app.agent.runner.Runner.run", new=AsyncMock(side_effect=fake_runner)):
        response = await run_supplymate(f"¿Cuánto debería pedir de {SKU_HIGH_QTY}?")

    assert isinstance(response, ChatResponse)
    assert response.product_id == SKU_HIGH_QTY
    assert response.recommended_quantity == expected.recommended_quantity
    assert response.recommended_quantity == 173


@pytest.mark.asyncio
async def test_explain_orphan_falls_back_to_deterministic_text():
    ctx = _seed_context_for_high_qty()
    expected = catalog_service.get_replenishment_recommendation(SKU_HIGH_QTY)

    async def fake_runner(agent, message, context=None, **kwargs):
        class Result:
            final_output = "Recomiendo pedir 999 unidades inventadas."

        if context is not None and hasattr(agent, "tools") and agent.tools:
            context.product_id = ctx.product_id
            context.inventory = ctx.inventory
            context.sales = ctx.sales
            context.params = ctx.params
        return Result()

    with patch("app.agent.runner.Runner.run", new=AsyncMock(side_effect=fake_runner)):
        response = await run_supplymate(f"¿Cuánto debería pedir de {SKU_HIGH_QTY}?")

    assert "999" not in response.answer
    assert str(expected.recommended_quantity) in response.answer
    assert "order-up-to" in response.answer.lower()


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

    with patch("app.agent.runner.Runner.run", new=AsyncMock(side_effect=fake_runner)):
        response = await run_supplymate(f"¿Cuánto pedir de {SKU_ZERO_QTY}?")

    assert response.recommended_quantity == 0
    assert response.product_id == SKU_ZERO_QTY


@pytest.mark.asyncio
async def test_run_supplymate_unknown_product():
    async def fake_runner(agent, message, context=None, **kwargs):
        class Result:
            final_output = "No encontré el producto."

        return Result()

    with patch("app.agent.runner.Runner.run", new=AsyncMock(side_effect=fake_runner)):
        with pytest.raises(ProductNotFoundError):
            await run_supplymate(f"¿Cuánto pedir de {SKU_UNKNOWN}?")


@pytest.mark.asyncio
async def test_run_supplymate_purchase_list():
    response = await run_supplymate("¿Qué productos tengo que comprar?")
    assert response.mode == "list"
    assert response.purchase_list
    assert len(response.purchase_list) <= 25
    assert all(item.recommended_quantity > 0 for item in response.purchase_list)
    assert response.dashboard is not None
    assert response.dashboard.skus > 0
    assert "productos" in response.answer.lower()


@pytest.mark.asyncio
async def test_run_supplymate_top_categories():
    response = await run_supplymate("cuales son las categorias mas vendidas")
    assert response.mode == "sales"
    assert response.dashboard is not None
    assert response.dashboard.by_sales
    assert response.dashboard.by_sales[0].units_sold >= response.dashboard.by_sales[-1].units_sold
    assert "categor" in response.answer.lower()


@pytest.mark.asyncio
async def test_fallback_hydrates_when_agent_skips_tools():
    expected = catalog_service.get_replenishment_recommendation(SKU_HIGH_QTY)

    async def fake_runner(agent, message, context=None, **kwargs):
        class Result:
            final_output = f"Recomiendo pedir {expected.recommended_quantity}."

        return Result()

    with patch("app.agent.runner.Runner.run", new=AsyncMock(side_effect=fake_runner)):
        response = await run_supplymate(f"cuanto pedir de {SKU_HIGH_QTY}")

    assert response.product_id == SKU_HIGH_QTY
    assert response.recommended_quantity == expected.recommended_quantity


@pytest.mark.asyncio
async def test_run_supplymate_explore_jabones():
    response = await run_supplymate("¿Cuántos jabones debo comprar?")
    assert response.mode == "explore"
    assert response.scope is not None
    assert "Jabon de Tocador" in response.scope.categories
    assert response.group_summaries
    assert "Entendí" in response.answer


@pytest.mark.asyncio
async def test_run_supplymate_explore_jabones_and_shampoo():
    response = await run_supplymate("¿Cuántos jabones y shampoo debo comprar?")
    assert response.mode == "explore"
    assert response.scope is not None
    assert "Jabon de Tocador" in response.scope.categories
    assert "Shampoo" in response.scope.subcategories
    assert len(response.group_summaries) >= 2


@pytest.mark.asyncio
async def test_run_supplymate_explore_panales_xxg():
    response = await run_supplymate("me refiero a pañales xxg")
    assert response.mode == "explore"
    assert response.scope is not None
    assert any("Pañal" in c for c in response.scope.categories)
    assert "xxg" in response.scope.name_tokens
    assert response.purchase_list


@pytest.mark.asyncio
async def test_run_supplymate_disambiguation():
    response = await run_supplymate("¿Cuánto cuidado debo comprar?")
    assert response.mode == "disambiguation"
    assert response.interpretation is not None
    assert response.interpretation.disambiguation_options


@pytest.mark.asyncio
async def test_run_supplymate_inventory_risk():
    response = await run_supplymate("¿Qué jabones tienen riesgo?")
    assert response.mode == "explore"
    assert response.scope is not None
    assert "stockout_risk" in response.scope.health_buckets


@pytest.mark.asyncio
async def test_regex_purchase_does_not_call_classifier():
    with patch(
        "app.agent.runner.classify_intent",
        new=AsyncMock(side_effect=AssertionError("classifier should not run")),
    ):
        response = await run_supplymate("¿Qué productos tengo que comprar?")
    assert response.mode == "list"


@pytest.mark.asyncio
async def test_llm_classifies_stockout_paraphrase_as_purchase_list():
    with patch(
        "app.pipeline.query_interpreter_agent.interpret_query_llm",
        new=AsyncMock(return_value=None),
    ):
        with patch("app.agent.runner.classify_intent", new=AsyncMock(return_value="purchase_list")):
            response = await run_supplymate("qué me está faltando del depósito")
    assert response.mode == "list"
    assert response.dashboard is not None
    assert response.purchase_list


@pytest.mark.asyncio
async def test_llm_classifies_sales_paraphrase():
    with patch("app.agent.runner.classify_intent", new=AsyncMock(return_value="sales_categories")):
        response = await run_supplymate("qué rubros mueven más unidades")
    assert response.mode == "sales"
    assert response.dashboard is not None
    assert response.dashboard.by_sales


@pytest.mark.asyncio
async def test_llm_unknown_does_not_force_a_random_sku():
    with patch("app.agent.runner.classify_intent", new=AsyncMock(return_value="unknown")):
        with pytest.raises(ProductNotFoundError):
            await run_supplymate("hola cómo va el día")


@pytest.mark.asyncio
async def test_run_analyze_priorities_subset_of_purchase_list():
    import json

    from app.agent import run_analyze
    from app.core.models import AnalyzeRequest, AnalyticalScope
    from app.services.insight import insight_cache

    insight_cache.reset()
    scope = AnalyticalScope()
    slice_data = catalog_service.replenishment_slice(scope, limit=25)
    if not slice_data.purchase_list:
        pytest.skip("empty purchase list")
    item = slice_data.purchase_list[0]
    n = len(slice_data.purchase_list)
    total = sum(i.recommended_quantity for i in slice_data.purchase_list)
    payload = {
        "panel_title": "T",
        "summary": f"{n} productos",
        "bullets": [f"{n} SKUs · {total} unidades"],
        "purchase_priorities": [
            {
                "product_id": item.product_id,
                "product_name": item.product_name,
                "recommended_quantity": item.recommended_quantity,
                "reason": "x",
            }
        ],
        "navigation_hints": [],
        "suggested_questions": [],
        "highlight_kpis": [],
    }

    async def fake_run(agent, prompt, **kwargs):
        class Result:
            final_output = json.dumps(payload)

        return Result()

    with patch("app.agent.runner.Runner.run", new=AsyncMock(side_effect=fake_run)):
        response = await run_analyze(
            AnalyzeRequest(mode="explore", scope=scope, root_question="q")
        )
    assert response.insight_source == "llm"
    assert response.insight is not None
    ids = {p.product_id for p in response.insight.purchase_priorities}
    assert ids <= {i.product_id for i in response.purchase_list}
