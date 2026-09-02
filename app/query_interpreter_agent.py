from __future__ import annotations

import json
import time

from agents import Agent, Runner

from app.llm_log import emit
from app.models import QueryInterpretation, Reference
from app.query_interpretation import interpret_query_rules, normalize_text

INTERPRETER_INSTRUCTIONS = """
Sos un intérprete de consultas para SupplyMate (reposición de inventario).

Extraé la intención y las referencias del usuario en español. Respondé SOLO JSON válido:

{
  "intent": "replenishment" | "inventory_risk" | "sales_ranking" | "single_sku" | "unknown",
  "references": [{"text": "...", "kind": "product_group"|"sku_hint"|"filter_hint"}],
  "filter_hints": ["riesgo", "quiebre", ...],
  "confidence": "high" | "low",
  "relation": "new_query" | "refinement"
}

Reglas:
- references: sustantivos/rubros que nombra el usuario (ej. jabones, shampoo, xxg). NO nombres de categoría interna del catálogo.
- Un talle o variante (xxg, xxxg) es product_group, no single_sku.
- relation=refinement si el usuario recorta el análisis actual (me refiero a, sólo, los de, un talle).
- relation=new_query si cambia de rubro (pañales → shampoo).
- Si no hay suficiente contexto para responder bien, igual extraé la referencia y usá replenishment + refinement; Python guía las opciones.
- replenishment: cuánto comprar/pedir/reponer, o un recorte de rubro/talle.
- inventory_risk: riesgo, quiebre, sin stock sobre un alcance.
- sales_ranking: categorías más vendidas.
- single_sku: un producto concreto o código numérico.
- confidence low si el término es genérico (cuidado, baño, etc.).
- NUNCA inventes cantidades ni categorías internas del catálogo.
""".strip()


def _validate_references(message: str, refs: list[Reference]) -> list[Reference]:
    msg_norm = normalize_text(message)
    valid: list[Reference] = []
    for ref in refs:
        token = normalize_text(ref.text)
        if not token:
            continue
        if token in msg_norm or any(part in msg_norm for part in token.split()):
            valid.append(ref)
    return valid[:5]


def _parse_interpretation(raw: dict, message: str) -> QueryInterpretation | None:
    intent = str(raw.get("intent", "unknown")).lower().strip()
    if intent not in (
        "replenishment",
        "inventory_risk",
        "sales_ranking",
        "single_sku",
        "unknown",
    ):
        intent = "unknown"
    refs_raw = raw.get("references") or []
    refs: list[Reference] = []
    for item in refs_raw:
        if isinstance(item, dict) and item.get("text"):
            kind = item.get("kind", "product_group")
            if kind not in ("product_group", "sku_hint", "filter_hint"):
                kind = "product_group"
            refs.append(Reference(text=str(item["text"])[:80], kind=kind))
    refs = _validate_references(message, refs)
    hints = [str(h) for h in (raw.get("filter_hints") or [])][:5]
    confidence = raw.get("confidence", "high")
    if confidence not in ("high", "low"):
        confidence = "high"
    return QueryInterpretation(
        intent=intent,  # type: ignore[arg-type]
        references=refs,
        filter_hints=hints,
        confidence=confidence,  # type: ignore[arg-type]
        source="llm",
    )


async def interpret_query_llm(message: str, previous_scope=None) -> QueryInterpretation | None:
    ruled = interpret_query_rules(message, previous_scope)
    if ruled is not None and ruled.intent != "unknown":
        return ruled

    try:
        from app.agent import get_model

        agent = Agent(
            name="SupplyMateQueryInterpreter",
            instructions=INTERPRETER_INSTRUCTIONS,
            model=get_model(),
        )
        started = time.perf_counter()
        result = await Runner.run(agent, f"Consulta del usuario:\n{message.strip()}")
        latency_ms = int((time.perf_counter() - started) * 1000)
        emit(
            event="runner.run",
            agent="SupplyMateQueryInterpreter",
            latency_ms=latency_ms,
        )
        text = str(result.final_output).strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        raw = json.loads(text)
        return _parse_interpretation(raw, message)
    except Exception:
        emit(
            event="runner.run",
            agent="SupplyMateQueryInterpreter",
            latency_ms=0,
            fallback_used=True,
        )
        return None
