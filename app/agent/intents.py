from __future__ import annotations

import re
import unicodedata
from typing import Literal

Intent = Literal["purchase_list", "sales_categories", "single_product", "unknown"]

VALID_INTENTS: tuple[Intent, ...] = (
    "purchase_list",
    "sales_categories",
    "single_product",
    "unknown",
)

_INTENT_ALIASES = {
    "replenish_list": "purchase_list",
    "inventory_health": "purchase_list",
    "dashboard": "purchase_list",
    "top_categories": "sales_categories",
    "single_sku": "single_product",
}

# Flexible patterns: tolerate typos (comprra, pedirr) via \w* stems.
PURCHASE_LIST_PATTERNS = (
    re.compile(r"\blista de (compra|pedido|reposicion|reabastecimiento)\b"),
    re.compile(r"\bproductos?\b.*\b(compr\w*|ped\w*|repon\w*|falta|faltan|faltante|quiebre)\b"),
    re.compile(r"\b(compr\w*|ped\w*|repon\w*|falta|faltan|faltante|quiebre)\b.*\bproductos?\b"),
    re.compile(
        r"\b(que|qué|cuales|cuales)\b.*\b(debo|deberia|debería|necesito|tengo|hay)\b.*\b(compr\w*|ped\w*|repon\w*)\b"
    ),
    re.compile(r"\bmostr(a|á|ame)\b.*\b(compr\w*|ped\w*)\b"),
    re.compile(r"\ben falta\b"),
    re.compile(r"\bsin stock\b"),
    re.compile(r"\briesgo de quiebre\b"),
)


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9? ]+", " ", text)
    return " ".join(text.split())


DASHBOARD_PATTERNS = (
    re.compile(r"\bdashboard\b"),
    re.compile(r"\bque esta pasando\b"),
    re.compile(r"\bsalud\b.*\binventario\b"),
    re.compile(r"\binventario\b.*\bsalud\b"),
    re.compile(r"\bkpis?\b"),
)

SALES_CATEGORY_PATTERNS = (
    re.compile(r"\bcategor\w*\b.*\bvend"),
    re.compile(r"\bvend\w*\b.*\bcategor"),
    re.compile(r"\btop categor"),
    re.compile(r"\bque categor\w*\b.*\b(mas|vende|venden)"),
)


def is_top_categories_query(message: str) -> bool:
    msg = _normalize(message)
    if not msg:
        return False
    if msg.endswith("?"):
        msg = msg[:-1].strip()
    return any(pattern.search(msg) for pattern in SALES_CATEGORY_PATTERNS)


def is_purchase_list_query(message: str) -> bool:
    """True when the user asks for a replenishment list or inventory dashboard."""
    msg = _normalize(message)
    if not msg:
        return False
    if msg.endswith("?"):
        msg = msg[:-1].strip()
    if any(pattern.search(msg) for pattern in DASHBOARD_PATTERNS):
        return True
    return any(pattern.search(msg) for pattern in PURCHASE_LIST_PATTERNS)


def match_rule_intent(message: str) -> Intent | None:
    """Cheap regex router. None means the concept was not recognized."""
    if is_top_categories_query(message):
        return "sales_categories"
    if is_purchase_list_query(message):
        return "purchase_list"
    return None


def parse_intent_label(text: str) -> Intent:
    """Extract a single intent label from noisy LLM output."""
    raw = (text or "").strip().lower().replace("-", "_")
    if not raw:
        return "unknown"

    first_line = raw.splitlines()[0].strip()
    token = re.split(r"[^a-z_]+", first_line, maxsplit=1)[0]
    if token in VALID_INTENTS:
        return token  # type: ignore[return-value]
    if token in _INTENT_ALIASES:
        return _INTENT_ALIASES[token]  # type: ignore[return-value]

    normalized = re.sub(r"[^a-z_]+", "_", raw)
    for label in ("purchase_list", "sales_categories", "single_product"):
        if label in normalized:
            return label
    for alias, label in _INTENT_ALIASES.items():
        if alias in normalized:
            return label  # type: ignore[return-value]
    return "unknown"
