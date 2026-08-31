from __future__ import annotations

import re

from app.intents import is_purchase_list_query, is_top_categories_query
from app.models import BusinessIntent, QueryInterpretation, Reference
from app.products import NUMERIC_CODE_RE, message_looks_like_sku
from app.reference_resolver import normalize_text, _QUERY_STOPWORDS

_PURCHASE_VERB_RE = re.compile(r"\b(compr\w*|ped\w*|repon\w*)\b")
_QUANTITY_RE = re.compile(r"\bcuant[oa]s?\b")
_RISK_HINTS = ("riesgo", "quiebre", "sin stock", "en falta", "faltante")
_SPLIT_RE = re.compile(r"\s+y\s+|\s*,\s*")


def _extract_filter_hints(message: str) -> list[str]:
    msg = normalize_text(message)
    return [hint for hint in _RISK_HINTS if hint in msg]


def _has_risk_intent(message: str) -> bool:
    msg = normalize_text(message)
    return any(hint in msg for hint in _RISK_HINTS)


def _extract_entity_tokens(message: str) -> list[str]:
    msg = normalize_text(message)
    if msg.endswith("?"):
        msg = msg[:-1].strip()
    tokens = [
        t
        for t in msg.split()
        if t not in _QUERY_STOPWORDS and len(t) >= 3
    ]
    if not tokens:
        return []
    if _QUANTITY_RE.search(msg) or _PURCHASE_VERB_RE.search(msg):
        return tokens
    return []


def _split_reference_phrases(message: str) -> list[str]:
    msg = normalize_text(message)
    if msg.endswith("?"):
        msg = msg[:-1].strip()
    for prefix in (
        r"^cuant[oa]s?\s+",
        r"^cuanto\s+",
        r"^que\s+",
        r"^qué\s+",
    ):
        msg = re.sub(prefix, "", msg)
    msg = re.sub(
        r"\b(debo|deberia|debería|tengo|necesito|hay)\s+(que\s+)?(compr\w*|ped\w*|repon\w*)\s*",
        "",
        msg,
    )
    msg = re.sub(r"\b(tienen|tiene)\s+(riesgo|quiebre)\b", "", msg)
    msg = re.sub(r"\b(riesgo|quiebre)\s*$", "", msg).strip()
    msg = re.sub(r"\b(compr\w*|ped\w*|repon\w*)\s*$", "", msg).strip()
    msg = re.sub(r"^de\s+", "", msg).strip()
    if not msg:
        return []
    parts = _SPLIT_RE.split(msg)
    refs: list[str] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        part_tokens = [t for t in part.split() if t not in _QUERY_STOPWORDS and len(t) >= 3]
        if part_tokens:
            refs.append(" ".join(part_tokens))
    return refs


def _references_from_message(message: str) -> list[Reference]:
    refs: list[Reference] = []
    for phrase in _split_reference_phrases(message):
        kind: str = "sku_hint" if NUMERIC_CODE_RE.fullmatch(phrase.strip()) else "product_group"
        refs.append(Reference(text=phrase, kind=kind))  # type: ignore[arg-type]
    if refs:
        return refs[:5]
    for token in _extract_entity_tokens(message):
        if token not in _RISK_HINTS:
            kind = "sku_hint" if NUMERIC_CODE_RE.fullmatch(token) else "product_group"
            refs.append(Reference(text=token, kind=kind))  # type: ignore[arg-type]
    return refs[:5]


def interpret_query_rules(message: str) -> QueryInterpretation | None:
    text = (message or "").strip()
    if not text:
        return QueryInterpretation(intent="unknown")

    if is_top_categories_query(text):
        return QueryInterpretation(intent="sales_ranking", source="rules")

    filter_hints = _extract_filter_hints(text)
    refs = _references_from_message(text)

    if refs and all(NUMERIC_CODE_RE.fullmatch(r.text.strip()) for r in refs):
        return QueryInterpretation(
            intent="single_sku",
            references=refs,
            filter_hints=filter_hints,
            source="rules",
        )

    if message_looks_like_sku(text):
        sku_match = re.search(r"\d{5,}", text)
        if sku_match:
            return QueryInterpretation(
                intent="single_sku",
                references=[Reference(text=sku_match.group(0), kind="sku_hint")],
                filter_hints=filter_hints,
                source="rules",
            )

    if is_purchase_list_query(text) and not refs:
        if _has_risk_intent(text):
            return QueryInterpretation(
                intent="inventory_risk",
                filter_hints=filter_hints,
                source="rules",
            )
        return QueryInterpretation(intent="replenishment", source="rules")

    if refs and (_QUANTITY_RE.search(normalize_text(text)) or _PURCHASE_VERB_RE.search(normalize_text(text))):
        intent: BusinessIntent = "inventory_risk" if _has_risk_intent(text) else "replenishment"
        return QueryInterpretation(
            intent=intent,
            references=refs,
            filter_hints=filter_hints,
            source="rules",
        )

    if refs and _has_risk_intent(text):
        return QueryInterpretation(
            intent="inventory_risk",
            references=refs,
            filter_hints=filter_hints,
            source="rules",
        )

    return None


async def interpret_query(message: str) -> QueryInterpretation:
    ruled = interpret_query_rules(message)
    if ruled is not None:
        return ruled

    try:
        from app.query_interpreter_agent import interpret_query_llm

        llm_result = await interpret_query_llm(message)
        if llm_result is not None:
            return llm_result
    except Exception:
        pass

    return QueryInterpretation(intent="unknown", confidence="low", source="rules")
