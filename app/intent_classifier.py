from __future__ import annotations

import time

from agents import Agent, Runner

from app.intents import Intent, parse_intent_label
from app.llm_log import emit

CLASSIFY_INSTRUCTIONS = """
Sos un clasificador de intenciones para SupplyMate, un sistema de reposición de inventario.

El usuario escribe en español y puede tener typos. Clasificá el CONCEPTO de la pregunta, no las palabras exactas.

Respondé con UNA sola etiqueta, en minúsculas, sin explicación ni puntuación:

purchase_list
sales_categories
single_product
unknown

purchase_list: quiere ver qué hay que comprar, qué está en falta, sin stock, quiebre, reponer, lista de pedido, salud del inventario, dashboard, qué está pasando con el stock. No nombra un producto concreto.

sales_categories: ranking de categorías o rubros más vendidos.

single_product: pregunta por UN producto (nombre, marca, código, cuánto pedir de X).

unknown: saludo, fuera de tema, o no se puede decidir.

Ejemplos:
qué productos están en falta → purchase_list
los que se van a acabar → purchase_list
qué me está faltando → purchase_list
cuales estan por reventar → purchase_list
qué rubros venden más → sales_categories
cuánto pedir de 47 street aura → single_product
hola → unknown
""".strip()


def build_classifier_agent(model) -> Agent:
    return Agent(
        name="SupplyMateIntent",
        instructions=CLASSIFY_INSTRUCTIONS,
        model=model,
    )


async def classify_intent(message: str) -> Intent | None:
    """LLM concept router. None = classifier unavailable; caller should fall back."""
    text = (message or "").strip()
    if not text:
        return "unknown"
    try:
        from app.agent import get_model

        agent = build_classifier_agent(get_model())
        started = time.perf_counter()
        result = await Runner.run(agent, f"Pregunta del usuario:\n{text}")
        latency_ms = int((time.perf_counter() - started) * 1000)
        intent = parse_intent_label(str(result.final_output))
        emit(
            event="runner.run",
            agent="SupplyMateIntent",
            latency_ms=latency_ms,
            intent=intent,
        )
        return intent
    except Exception:
        emit(
            event="runner.run",
            agent="SupplyMateIntent",
            latency_ms=0,
            fallback_used=True,
        )
        return None
