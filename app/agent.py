from __future__ import annotations

import json

from agents import Agent, Runner, set_tracing_disabled
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from openai import AsyncOpenAI

from app import config
from app.intent_classifier import classify_intent
from app.intents import is_purchase_list_query, is_top_categories_query, match_rule_intent
from app.models import ChatResponse, ProductNotFoundError, SupplyContext
from app.products import message_looks_like_sku, resolve_from_message, resolve_product_id
from app.services import catalog_service
from app.tools import (
    get_inventory,
    get_replenishment_params,
    get_sales_history,
    load_inventory,
    load_replenishment_params,
    load_sales_history,
)

SUPPLY_INSTRUCTIONS = """
You are SupplyMate, a replenishment assistant for SME distributors.

The user may mention a product by catalog code, barcode, or product name.
When you can identify a product:
1. ALWAYS call get_inventory
2. ALWAYS call get_sales_history (days=30)
3. ALWAYS call get_replenishment_params
Call all three tools before finishing. Never invent stock, sales, or parameters.
""".strip()

EXPLAIN_INSTRUCTIONS = """
You are SupplyMate. Explain the replenishment recommendation in Spanish.
Use ONLY the numbers provided in the JSON payload.
Do not invent or change recommended_quantity.
Keep 3-5 short sentences for a warehouse manager.
Never use English metric names; say cantidad recomendada, demanda diaria, punto de reorden, stock de seguridad.
""".strip()

PURCHASE_LIST_LIMIT = 25

_model_cache: OpenAIChatCompletionsModel | str | None = None


def _extract_product_id(message: str) -> str | None:
    if is_purchase_list_query(message) or is_top_categories_query(message):
        return None
    return resolve_from_message(message)


def _hydrate_context(context: SupplyContext, product_id: str) -> None:
    product_id = resolve_product_id(product_id)
    context.product_id = product_id
    context.inventory = load_inventory(product_id)
    context.sales = load_sales_history(product_id, days=30)
    context.params = load_replenishment_params(product_id)


def get_model() -> OpenAIChatCompletionsModel | str:
    global _model_cache
    if _model_cache is not None:
        return _model_cache

    if config.LLM_PROVIDER == "groq":
        if not config.GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Get a free key at https://console.groq.com/keys"
            )
        set_tracing_disabled(True)
        client = AsyncOpenAI(
            api_key=config.GROQ_API_KEY,
            base_url=config.GROQ_BASE_URL,
        )
        _model_cache = OpenAIChatCompletionsModel(
            model=config.GROQ_MODEL,
            openai_client=client,
        )
        return _model_cache

    if not config.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    _model_cache = config.OPENAI_MODEL
    return _model_cache


def build_supply_agent() -> Agent:
    return Agent(
        name="SupplyMate",
        instructions=SUPPLY_INSTRUCTIONS,
        model=get_model(),
        tools=[get_inventory, get_sales_history, get_replenishment_params],
    )


def build_explain_agent() -> Agent:
    return Agent(
        name="SupplyMateExplainer",
        instructions=EXPLAIN_INSTRUCTIONS,
        model=get_model(),
    )


async def _run_top_categories() -> ChatResponse:
    snap, _items = catalog_service.chat_dashboard(limit=1)
    return ChatResponse(
        answer=catalog_service.format_sales_answer(snap),
        mode="sales",
        dashboard=snap,
    )


async def _run_purchase_list(message: str) -> ChatResponse:
    snap, items = catalog_service.chat_dashboard(limit=PURCHASE_LIST_LIMIT)
    return ChatResponse(
        answer=catalog_service.format_dashboard_answer(snap, items),
        mode="list",
        purchase_list=items,
        dashboard=snap,
    )


async def _run_single_product(message: str) -> ChatResponse:
    product_id = _extract_product_id(message)
    context = SupplyContext(product_id=product_id)
    supply_agent = build_supply_agent()

    await Runner.run(supply_agent, message, context=context)

    if not context.ready():
        product_id = context.product_id or _extract_product_id(message)
        if not product_id:
            raise ProductNotFoundError(
                "UNKNOWN — no se detectó un producto. "
                "Escribí el nombre del producto o preguntá qué productos tenés que comprar."
            )
        _hydrate_context(context, product_id)

    assert context.inventory is not None
    product_id = context.inventory.product_id
    recommendation = catalog_service.get_replenishment_recommendation(product_id)
    context.result = recommendation.calculation
    context.recommendation = recommendation

    explain_agent = build_explain_agent()
    explain_payload = {
        "product_id": recommendation.product_id,
        "product_name": recommendation.product_name,
        "recommended_quantity": recommendation.recommended_quantity,
        "calculation": recommendation.calculation.model_dump(mode="json"),
        "context": recommendation.context.model_dump(mode="json"),
    }
    explain_prompt = (
        "Explica esta recomendación de reabastecimiento al usuario:\n"
        f"{json.dumps(explain_payload, ensure_ascii=False)}"
    )
    explain_run = await Runner.run(explain_agent, explain_prompt)
    answer = str(explain_run.final_output)

    return ChatResponse(
        answer=answer,
        mode="single",
        product_id=recommendation.product_id,
        product_name=recommendation.product_name,
        recommended_quantity=recommendation.recommended_quantity,
        calculation=recommendation.calculation,
        context=recommendation.context,
    )


async def run_supplymate(message: str) -> ChatResponse:
    """Route by concept, then let deterministic Python compute numbers.

    1. Regex fast-path (no LLM).
    2. Numeric SKU in the message → single product.
    3. LLM classifies the concept (falta de stock vs un SKU vs ranking).
    4. If the classifier is down, fall back to product resolution.
    """
    rule = match_rule_intent(message)
    if rule == "sales_categories":
        return await _run_top_categories()
    if rule == "purchase_list":
        return await _run_purchase_list(message)

    if message_looks_like_sku(message):
        return await _run_single_product(message)

    intent = await classify_intent(message)
    if intent == "sales_categories":
        return await _run_top_categories()
    if intent == "purchase_list":
        return await _run_purchase_list(message)
    if intent == "single_product":
        return await _run_single_product(message)
    if intent is None:
        return await _run_single_product(message)

    raise ProductNotFoundError(
        "No entendí si preguntás por un producto o por la lista de reposición. "
        "Probá: «qué productos están en falta» o el nombre / código del producto."
    )
