from __future__ import annotations

import re

from app.agent.intents import is_purchase_list_query, is_top_categories_query
from app.core.models import AnalyticalScope, BusinessIntent, QueryInterpretation, QueryRelation, Reference
from app.catalog.products import NUMERIC_CODE_RE, message_looks_like_sku
from app.pipeline.reference_resolver import normalize_text, _QUERY_STOPWORDS, SIZE_TOKEN_RE
from app.services.analytics.dashboard import COVERAGE_ORDER

_PURCHASE_VERB_RE = re.compile(r"\b(compr\w*|ped\w*|repon\w*)\b")
_QUANTITY_RE = re.compile(r"\bcuant[oa]s?\b")
_DISCOURSE_RE = re.compile(r"\bme\s+refer\w*\s+(a\s+)?")
_TALLE_RE = re.compile(r"\b(de\s+)?(talle|talla)\b")
_REFINEMENT_RE = re.compile(
    r"\b(me\s+refer\w*|quise\s+decir|hablo\s+de|los\s+de|las\s+de|"
    r"el\s+de|la\s+de|s[oó]lo|solamente|pero\b|y\s+los|y\s+las)\b"
)
_RISK_HINTS = (
    "riesgo",
    "quiebre",
    "sin stock",
    "en falta",
    "faltante",
    "critico",
    "criticos",
    "critica",
    "criticas",
)
_FILTER_STOPWORDS = frozenset(
    {
        "mostrame",
        "mostrar",
        "ordena",
        "ordenalos",
        "ordenar",
        "unidades",
        "cobertura",
        "dias",
        "menos",
        "tengan",
        "tenga",
        "critico",
        "criticos",
        "critica",
        "criticas",
        "riesgo",
        "quiebre",
        "faltante",
        "pedir",
        "pedido",
    }
)
_SPLIT_RE = re.compile(r"\s+y\s+|\s*,\s*")
# Coverage: «menos de 3 días», «0-3», «0–3», «cobertura 3»
_COVERAGE_LT_RE = re.compile(
    r"(?:menos\s+de|menos\s+que|bajo|menor\s+(?:a|de)|<\s*)\s*(\d+)\s*d[ií]as?",
    re.IGNORECASE,
)
_COVERAGE_RANGE_RE = re.compile(
    r"\b(\d+)\s*[-–]\s*(\d+)\s*d[ií]as?\b",
    re.IGNORECASE,
)
_COVERAGE_N_RE = re.compile(
    r"\bcobertura\s+(?:de\s+)?(\d+)\s*d[ií]as?\b",
    re.IGNORECASE,
)


def coverage_bucket_from_days_threshold(days: int, *, exclusive_lt: bool = True) -> str | None:
    """Map a day threshold to a COVERAGE_ORDER band."""
    if exclusive_lt:
        if days <= 3:
            return "0–3 días"
        if days <= 7:
            return "3–7 días"
        if days <= 14:
            return "7–14 días"
        if days <= 30:
            return "14–30 días"
        return "30+ días"
    # Inclusive range start already handled by range matcher.
    return None


def extract_coverage_bucket(message: str) -> str | None:
    """Python-owned coverage band from NL (LLM must not invent the bucket)."""
    raw = message or ""
    msg = normalize_text(raw)
    # Explicit en-dash / hyphen bands first
    for band in COVERAGE_ORDER:
        band_norm = normalize_text(band)
        if band_norm and band_norm in msg:
            return band
        # Allow "0-3 dias" without en-dash
        alt = band_norm.replace(" ", "")
        compact = msg.replace(" ", "")
        if alt and alt in compact:
            return band

    lt = _COVERAGE_LT_RE.search(raw) or _COVERAGE_LT_RE.search(msg)
    if lt:
        return coverage_bucket_from_days_threshold(int(lt.group(1)), exclusive_lt=True)

    rng = _COVERAGE_RANGE_RE.search(raw) or _COVERAGE_RANGE_RE.search(msg)
    if rng:
        lo, hi = int(rng.group(1)), int(rng.group(2))
        label = f"{lo}–{hi} días"
        if label in COVERAGE_ORDER:
            return label
        # Fall back: use upper bound as exclusive threshold proxy
        return coverage_bucket_from_days_threshold(hi, exclusive_lt=True)

    cov_n = _COVERAGE_N_RE.search(raw) or _COVERAGE_N_RE.search(msg)
    if cov_n:
        return coverage_bucket_from_days_threshold(int(cov_n.group(1)), exclusive_lt=True)
    return None


def _extract_filter_hints(message: str) -> list[str]:
    msg = normalize_text(message)
    hints: list[str] = [hint for hint in _RISK_HINTS if hint in msg]
    bucket = extract_coverage_bucket(message)
    if bucket and bucket not in hints:
        hints.append(bucket)
    return hints[:5]


def _has_risk_intent(message: str) -> bool:
    msg = normalize_text(message)
    return any(hint in msg for hint in _RISK_HINTS)


def _has_size_or_refinement(message: str, refs: list[Reference]) -> bool:
    msg = normalize_text(message)
    if _DISCOURSE_RE.search(msg) or _REFINEMENT_RE.search(msg):
        return True
    for ref in refs:
        if any(SIZE_TOKEN_RE.fullmatch(t) for t in normalize_text(ref.text).split()):
            return True
    return False


def _scope_empty(scope: AnalyticalScope | None) -> bool:
    if scope is None:
        return True
    return not any(
        (
            scope.categories,
            scope.subcategories,
            scope.coverage_buckets,
            scope.health_buckets,
            scope.suppliers,
            scope.name_tokens,
        )
    )


def classify_relation(message: str, previous_scope: AnalyticalScope | None) -> QueryRelation:
    if _scope_empty(previous_scope):
        return "new_query"
    msg = normalize_text(message)
    if _REFINEMENT_RE.search(msg):
        return "refinement"
    tokens = [t for t in msg.split() if t not in _QUERY_STOPWORDS and len(t) >= 2]
    if any(SIZE_TOKEN_RE.fullmatch(t) for t in tokens):
        return "refinement"
    if msg in {"todos", "todo", "todas"}:
        return "refinement"
    if (
        len(tokens) <= 2
        and not _QUANTITY_RE.search(msg)
        and not _PURCHASE_VERB_RE.search(msg)
        and not is_purchase_list_query(message)
        and not is_top_categories_query(message)
    ):
        return "refinement"
    return "new_query"


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
    msg = _DISCOURSE_RE.sub(" ", msg)
    msg = _TALLE_RE.sub(" ", msg)
    # Strip coverage / filter clauses so they never become product_group refs.
    msg = _COVERAGE_LT_RE.sub(" ", msg)
    msg = _COVERAGE_RANGE_RE.sub(" ", msg)
    msg = _COVERAGE_N_RE.sub(" ", msg)
    msg = re.sub(r"\bcobertura\b", " ", msg)
    msg = " ".join(msg.split())
    for prefix in (
        r"^cuant[oa]s?\s+",
        r"^cuanto\s+",
        r"^que\s+",
        r"^qué\s+",
        r"^mostrame\s+",
        r"^mostrar\s+",
    ):
        msg = re.sub(prefix, "", msg)
    msg = re.sub(
        r"\b(debo|deberia|debería|tengo|necesito|hay)\s+(que\s+)?(compr\w*|ped\w*|repon\w*)\s*",
        "",
        msg,
    )
    msg = re.sub(r"\b(tienen|tiene)\s+(riesgo|quiebre)\b", "", msg)
    msg = re.sub(r"\b(riesgo|quiebre|criticos?|criticas?)\s*$", "", msg).strip()
    msg = re.sub(r"\b(compr\w*|ped\w*|repon\w*|orden\w*)\s*$", "", msg).strip()
    msg = re.sub(r"^de\s+", "", msg).strip()
    if not msg:
        return []
    parts = _SPLIT_RE.split(msg)
    refs: list[str] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        part_tokens = [
            t
            for t in part.split()
            if t not in _QUERY_STOPWORDS
            and t not in _FILTER_STOPWORDS
            and (len(t) >= 3 or SIZE_TOKEN_RE.fullmatch(t))
        ]
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
        if token in _RISK_HINTS or token in _FILTER_STOPWORDS:
            continue
        kind = "sku_hint" if NUMERIC_CODE_RE.fullmatch(token) else "product_group"
        refs.append(Reference(text=token, kind=kind))  # type: ignore[arg-type]
    return refs[:5]


def interpret_query_rules(
    message: str,
    previous_scope: AnalyticalScope | None = None,
) -> QueryInterpretation | None:
    text = (message or "").strip()
    if not text:
        return QueryInterpretation(intent="unknown")

    relation = classify_relation(text, previous_scope)

    if is_top_categories_query(text):
        return QueryInterpretation(intent="sales_ranking", source="rules", relation="new_query")

    filter_hints = _extract_filter_hints(text)
    refs = _references_from_message(text)

    if refs and all(NUMERIC_CODE_RE.fullmatch(r.text.strip()) for r in refs):
        return QueryInterpretation(
            intent="single_sku",
            references=refs,
            filter_hints=filter_hints,
            source="rules",
            relation="new_query",
        )

    if message_looks_like_sku(text):
        sku_match = re.search(r"\d{5,}", text)
        if sku_match:
            return QueryInterpretation(
                intent="single_sku",
                references=[Reference(text=sku_match.group(0), kind="sku_hint")],
                filter_hints=filter_hints,
                source="rules",
                relation="new_query",
            )

    if is_purchase_list_query(text) and not refs:
        if _has_risk_intent(text):
            return QueryInterpretation(
                intent="inventory_risk",
                filter_hints=filter_hints,
                source="rules",
                relation=relation,
            )
        return QueryInterpretation(
            intent="replenishment",
            filter_hints=filter_hints,
            source="rules",
            relation=relation,
        )

    if refs and (
        _QUANTITY_RE.search(normalize_text(text))
        or _PURCHASE_VERB_RE.search(normalize_text(text))
        or _has_risk_intent(text)
        or _has_size_or_refinement(text, refs)
        or relation == "refinement"
        or is_purchase_list_query(text)
    ):
        intent: BusinessIntent = "inventory_risk" if _has_risk_intent(text) else "replenishment"
        return QueryInterpretation(
            intent=intent,
            references=refs,
            filter_hints=filter_hints,
            source="rules",
            relation=relation,
        )

    if relation == "refinement":
        return QueryInterpretation(
            intent="replenishment",
            references=refs,
            filter_hints=filter_hints,
            source="rules",
            relation="refinement",
        )

    return None


def enrich_interpretation_from_message(
    interpretation: QueryInterpretation,
    message: str,
) -> QueryInterpretation:
    """Merge Python-owned filter hints (coverage, críticos) onto LLM/rules output."""
    py_hints = _extract_filter_hints(message)
    merged = list(dict.fromkeys([*(interpretation.filter_hints or []), *py_hints]))[:5]
    intent = interpretation.intent
    if _has_risk_intent(message) and intent in ("replenishment", "unknown"):
        intent = "inventory_risk"
    if merged == list(interpretation.filter_hints or []) and intent == interpretation.intent:
        return interpretation
    return interpretation.model_copy(update={"filter_hints": merged, "intent": intent})


async def interpret_query(
    message: str,
    previous_scope: AnalyticalScope | None = None,
) -> QueryInterpretation:
    """Free-text chat always goes through the LLM; rules are only a fallback.

    Static filters/chips never call this — they apply scope without reinterpretation.
    """
    relation = classify_relation(message, previous_scope)
    try:
        from app.pipeline.query_interpreter_agent import interpret_query_llm

        llm_result = await interpret_query_llm(
            message, previous_scope, force=True
        )
        if llm_result is not None:
            enriched = enrich_interpretation_from_message(llm_result, message)
            return enriched.model_copy(update={"relation": relation})
    except Exception:
        pass

    ruled = interpret_query_rules(message, previous_scope)
    if ruled is not None:
        enriched = enrich_interpretation_from_message(ruled, message)
        return enriched.model_copy(update={"relation": relation})

    unknown = QueryInterpretation(
        intent="unknown",
        confidence="low",
        source="rules",
        relation=relation,
    )
    return enrich_interpretation_from_message(unknown, message)
