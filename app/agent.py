from __future__ import annotations

import json

from agents import Agent, Runner, set_tracing_disabled
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from openai import AsyncOpenAI

from app import config
from app.intent_classifier import classify_intent
from app.intents import is_purchase_list_query, is_top_categories_query, match_rule_intent
from app.models import (
    AnalyticalScope,
    AnalyzeRequest,
    AnalyzeResponse,
    ChatResponse,
    CommitSummary,
    DashboardInsight,
    ProductNotFoundError,
    SupplyContext,
)
from app.products import message_looks_like_sku, resolve_from_message, resolve_product_id
from app.services import catalog_service, insight_cache, prompt_compiler
from app.services import insight_validator
from app.services import panel_modes
from app.services import scope as scope_svc
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

INSIGHT_INSTRUCTIONS = """
You are SupplyMate Analista in EXPLORAR mode.
Respond ONLY with valid JSON for DashboardInsight. Spanish.
Use ONLY numbers from the user payload. Do not invent SKUs or quantities.
purchase_priorities must use product_id and recommended_quantity exactly from purchase_list_top.
""".strip()

COMMIT_INSTRUCTIONS = """
You are SupplyMate in ARMAR OC mode (confirmación).
Respond ONLY with valid JSON for CommitSummary. Spanish.
Use ONLY numbers from the payload. Do not suggest new filters.
top_priorities must match purchase_list_top SKUs and quantities exactly.
oc_summary must mention SKU count and total recommended units from the payload.
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


def build_insight_agent() -> Agent:
    return Agent(
        name="SupplyMateInsight",
        instructions=INSIGHT_INSTRUCTIONS,
        model=get_model(),
    )


def build_commit_agent() -> Agent:
    return Agent(
        name="SupplyMateCommit",
        instructions=COMMIT_INSTRUCTIONS,
        model=get_model(),
    )


def _parse_json_output(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text)


def _fallback_analyze_response(
    request: AnalyzeRequest,
    slice_data,
    *,
    prompt_hash: str = "",
) -> AnalyzeResponse:
    return AnalyzeResponse(
        mode=request.mode,
        scope=request.scope,
        frozen_scope=request.frozen_scope,
        evidence=slice_data.evidence,
        dashboard=slice_data.dashboard,
        purchase_list=slice_data.purchase_list,
        insight=None,
        commit_summary=None,
        insight_source="fallback",
        compiled_prompt_hash=prompt_hash,
    )


async def run_analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    panel_modes.validate_commit_request(
        request.mode, request.scope, request.frozen_scope
    )
    effective = panel_modes.effective_scope(
        request.mode, request.scope, request.frozen_scope
    )
    scope_key = scope_svc.cache_key(effective)
    ev_hash = insight_cache.events_hash(request.events)
    cache_key = insight_cache.cache_key(request.mode, scope_key, ev_hash)
    cached = insight_cache.get(cache_key)
    if cached is not None:
        return cached

    slice_data = catalog_service.replenishment_slice(effective, limit=25)
    root_dash, _ = catalog_service.chat_dashboard(limit=1, scope=AnalyticalScope())
    prompt = prompt_compiler.compile_analyze_prompt(
        mode=request.mode,
        root_question=request.root_question,
        events=request.events,
        slice_data=slice_data,
        root_dashboard=root_dash,
    )
    phash = prompt_compiler.prompt_hash(prompt)

    try:
        agent = (
            build_commit_agent()
            if request.mode == "commit"
            else build_insight_agent()
        )
        run = await Runner.run(agent, prompt)
        raw = _parse_json_output(str(run.final_output))
        if request.mode == "commit":
            summary = CommitSummary.model_validate(raw)
            errors = insight_validator.validate_commit_summary(summary, slice_data)
            if errors:
                response = _fallback_analyze_response(
                    request, slice_data, prompt_hash=phash
                )
            else:
                response = AnalyzeResponse(
                    mode=request.mode,
                    scope=request.scope,
                    frozen_scope=request.frozen_scope,
                    evidence=slice_data.evidence,
                    dashboard=slice_data.dashboard,
                    purchase_list=slice_data.purchase_list,
                    commit_summary=summary,
                    insight_source="llm",
                    compiled_prompt_hash=phash,
                )
        else:
            insight = DashboardInsight.model_validate(raw)
            errors = insight_validator.validate_insight(insight, slice_data)
            if errors:
                response = _fallback_analyze_response(
                    request, slice_data, prompt_hash=phash
                )
            else:
                response = AnalyzeResponse(
                    mode=request.mode,
                    scope=request.scope,
                    frozen_scope=request.frozen_scope,
                    evidence=slice_data.evidence,
                    dashboard=slice_data.dashboard,
                    purchase_list=slice_data.purchase_list,
                    insight=insight,
                    insight_source="llm",
                    compiled_prompt_hash=phash,
                )
    except (json.JSONDecodeError, ValueError, TypeError, RuntimeError):
        response = _fallback_analyze_response(request, slice_data, prompt_hash=phash)

    insight_cache.set(cache_key, response)
    return response


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
