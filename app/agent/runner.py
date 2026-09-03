from __future__ import annotations

import json
import time

from agents import Agent, Runner, set_tracing_disabled
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from openai import AsyncOpenAI

from app.core import config
from app.agent.explore_answer import (
    format_disambiguation_answer,
    format_explore_answer,
    group_summaries_from_resolved,
)
from app.guidance import guidance_after_slice, guidance_for_resolution
from app.agent.intent_classifier import classify_intent
from app.agent.intents import is_purchase_list_query, is_top_categories_query, match_rule_intent
from app.agent.llm_log import emit
from app.core.models import (
    AnalyticalScope,
    AnalyzeRequest,
    AnalyzeResponse,
    ChatInterpretation,
    ChatResponse,
    CommitSummary,
    DashboardInsight,
    GuidanceDecision,
    GuidanceChip,
    ProductNotFoundError,
    SupplyContext,
)
from app.catalog.products import NUMERIC_CODE_RE, message_looks_like_sku, resolve_from_message, resolve_product_id
from app.pipeline.query_interpretation import interpret_query
from app.pipeline.reference_resolver import resolve_references
from app.pipeline.scope_builder import build_resolution_result, promote_new_query_if_needed
from app.pipeline.query_interpretation import _scope_empty
from app.services import catalog_service, insight_cache, prompt_compiler
from app.services import insight_validator
from app.services import panel_modes
from app.services import scope as scope_svc
from app.agent.tools import (
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
If the payload includes related, you may mention complements using label and reason only.
Never claim transactional co-purchase (e.g. people who buy X usually buy Y).
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


async def _run_logged(agent, prompt, context=None, **kwargs):
    started = time.perf_counter()
    if context is not None:
        result = await Runner.run(agent, prompt, context=context, **kwargs)
    else:
        result = await Runner.run(agent, prompt, **kwargs)
    latency_ms = int((time.perf_counter() - started) * 1000)
    name = getattr(agent, "name", "unknown")
    emit(event="runner.run", agent=name, latency_ms=latency_ms)
    return result, latency_ms


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
        run, _latency = await _run_logged(agent, prompt)
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
    emit(
        event="analyze.complete",
        agent="SupplyMateCommit" if request.mode == "commit" else "SupplyMateInsight",
        latency_ms=0,
        fallback_used=response.insight_source == "fallback",
        insight_source=response.insight_source,
    )
    return response


async def _run_top_categories() -> ChatResponse:
    snap, _items = catalog_service.chat_dashboard(limit=1)
    return ChatResponse(
        answer=catalog_service.format_sales_answer(snap),
        mode="sales",
        dashboard=snap,
    )


async def _run_purchase_list(message: str, scope: AnalyticalScope | None = None) -> ChatResponse:
    active = scope or AnalyticalScope()
    slice_data = catalog_service.replenishment_slice(active, limit=PURCHASE_LIST_LIMIT)
    return ChatResponse(
        answer=catalog_service.format_dashboard_answer(
            slice_data.dashboard, slice_data.purchase_list
        ),
        mode="list",
        scope=active,
        purchase_list=slice_data.purchase_list,
        dashboard=slice_data.dashboard,
    )


async def _run_explore(
    message: str,
    scope: AnalyticalScope,
    *,
    interpretation: ChatInterpretation | None = None,
    group_summaries=None,
    guidance: GuidanceDecision | None = None,
) -> ChatResponse:
    slice_data = catalog_service.replenishment_slice(scope, limit=PURCHASE_LIST_LIMIT)
    chat_interp = interpretation or ChatInterpretation()
    summaries = group_summaries or []
    guide = guidance or slice_data.guidance or guidance_after_slice(slice_data)
    if guide.action in ("ask_clarification", "draft_oc"):
        chat_interp = chat_interp.model_copy(
            update={
                "guidance_question": guide.question,
                "guidance_options": guide.options,
            }
        )
    answer = format_explore_answer(slice_data, chat_interp, summaries, guide)
    return ChatResponse(
        answer=answer,
        mode="explore",
        scope=scope,
        interpretation=chat_interp,
        group_summaries=summaries,
        purchase_list=slice_data.purchase_list,
        dashboard=slice_data.dashboard,
        guidance=guide,
    )


async def _run_disambiguation(message: str, resolution) -> ChatResponse:
    question = (
        f"No estoy seguro de a qué te referís con "
        f"**«{resolution.resolved[0].user_text if resolution.resolved else 'eso'}»**."
    )
    options = resolution.disambiguation_options
    answer = format_disambiguation_answer(question, options)
    return ChatResponse(
        answer=answer,
        mode="disambiguation",
        interpretation=ChatInterpretation(
            confidence="low",
            disambiguation_question=question,
            disambiguation_options=options,
        ),
    )


async def _run_single_product(message: str) -> ChatResponse:
    product_id = _extract_product_id(message)
    context = SupplyContext(product_id=product_id)
    supply_agent = build_supply_agent()

    await _run_logged(supply_agent, message, context=context)

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
    explain_run, _latency = await _run_logged(explain_agent, explain_prompt)
    answer = str(explain_run.final_output)
    orphan_errors = insight_validator.validate_explanation_text(answer, explain_payload)
    fallback_used = bool(orphan_errors)
    if fallback_used:
        answer = catalog_service.format_single_product_answer(recommendation)
    emit(
        event="explain.complete",
        agent="SupplyMateExplainer",
        latency_ms=_latency,
        fallback_used=fallback_used,
        insight_source="fallback" if fallback_used else "llm",
    )

    return ChatResponse(
        answer=answer,
        mode="single",
        product_id=recommendation.product_id,
        product_name=recommendation.product_name,
        recommended_quantity=recommendation.recommended_quantity,
        calculation=recommendation.calculation,
        context=recommendation.context,
    )


async def run_apply_chip(
    scope: AnalyticalScope,
    chip: GuidanceChip,
) -> ChatResponse:
    from app.guidance.guidance_chips import apply_guidance_chip

    new_scope, enter_commit = apply_guidance_chip(scope, chip)
    response = await _run_explore(
        f"chip:{chip.label}",
        new_scope,
        interpretation=ChatInterpretation(
            understood_labels=_labels_from_scope(new_scope),
            relation="refinement",
        ),
    )
    if enter_commit:
        response = response.model_copy(
            update={
                "mode": "commit_ready",
            }
        )
    return response


async def run_supplymate(
    message: str,
    scope: AnalyticalScope | None = None,
    *,
    chip: GuidanceChip | None = None,
) -> ChatResponse:
    """Route by interpreted intent + catalog resolution, then deterministic Python."""
    if chip is not None:
        return await run_apply_chip(scope or AnalyticalScope(), chip)

    previous = scope
    interpretation = await interpret_query(message, previous_scope=previous)
    resolved = resolve_references(interpretation)
    interpretation = promote_new_query_if_needed(interpretation, resolved, previous)
    resolution = build_resolution_result(interpretation, resolved, previous)

    if resolution.blocking:
        unresolved_all = resolved and all(r.match_kind == "unresolved" for r in resolved)
        if (
            unresolved_all
            and interpretation.relation == "refinement"
            and not _scope_empty(previous)
        ):
            token = next((r.user_text for r in resolved if r.user_text), message)
            guide = guidance_for_resolution([], previous) if previous else GuidanceDecision()
            question = (
                f"No encontré productos relacionados con «{token}» en este recorte. "
                "Podés elegir una de estas opciones o preguntar por otro rubro."
            )
            options = guide.options or []
            return await _run_explore(
                message,
                previous,  # type: ignore[arg-type]
                interpretation=ChatInterpretation(
                    understood_labels=_labels_from_scope(previous),
                    relation="refinement",
                    guidance_question=question,
                    guidance_options=options,
                    confidence="low",
                ),
                guidance=GuidanceDecision(
                    action="ask_clarification",
                    reason="unresolved_refinement",
                    question=question,
                    options=options,
                ),
            )
        if interpretation.intent == "single_sku" or any(
            r.match_kind == "unresolved" and NUMERIC_CODE_RE.fullmatch(r.user_text.strip())
            for r in resolved
        ):
            sku = next(
                (r.user_text for r in resolved if r.user_text),
                message,
            )
            raise ProductNotFoundError(sku)
        if unresolved_all:
            token = next((r.user_text for r in resolved if r.user_text), message)
            raise ProductNotFoundError(token)
        return await _run_disambiguation(message, resolution)

    if interpretation.intent == "sales_ranking":
        return await _run_top_categories()

    exact = next((r for r in resolved if r.match_kind == "exact_sku"), None)
    if interpretation.intent == "single_sku" or exact:
        sku_message = f"cuanto pedir de {exact.product_id}" if exact else message
        if interpretation.intent == "single_sku" or exact or message_looks_like_sku(message):
            return await _run_single_product(sku_message)

    if interpretation.intent in ("replenishment", "inventory_risk"):
        if not interpretation.references:
            if interpretation.intent == "inventory_risk":
                return await _run_explore(
                    message,
                    resolution.scope,
                    interpretation=ChatInterpretation(
                        understood_labels=["Riesgo de quiebre"],
                        relation=interpretation.relation,
                    ),
                )
            return await _run_purchase_list(message, resolution.scope)

        summaries = group_summaries_from_resolved(resolved)
        labels = [s.label for s in summaries] or [
            r.label or r.user_text for r in resolved if r.match_kind == "group"
        ]
        if interpretation.relation == "refinement" and previous:
            labels = _labels_from_scope(resolution.scope) or labels
        guide = guidance_for_resolution(resolved, resolution.scope)
        return await _run_explore(
            message,
            resolution.scope,
            interpretation=ChatInterpretation(
                understood_labels=labels,
                confidence=interpretation.confidence,
                relation=interpretation.relation,
            ),
            group_summaries=summaries,
            guidance=guide,
        )

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


def _labels_from_scope(scope: AnalyticalScope | None) -> list[str]:
    if scope is None:
        return []
    labels = list(scope.categories) + list(scope.subcategories)
    labels.extend(t.upper() if t.islower() else t for t in scope.name_tokens)
    return labels
