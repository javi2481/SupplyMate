from __future__ import annotations

import re
import unicodedata

# Flexible patterns: tolerate typos (comprra, pedirr) via \w* stems.
PURCHASE_LIST_PATTERNS = (
    re.compile(r"\blista de (compra|pedido|reposicion|reabastecimiento)\b"),
    re.compile(r"\bproductos?\b.*\b(compr\w*|ped\w*|repon\w*)\b"),
    re.compile(r"\b(compr\w*|ped\w*|repon\w*)\b.*\bproductos?\b"),
    re.compile(
        r"\b(que|qué|cuales|cuales)\b.*\b(debo|deberia|debería|necesito|tengo|hay)\b.*\b(compr\w*|ped\w*|repon\w*)\b"
    ),
    re.compile(r"\bmostr(a|á|ame)\b.*\b(compr\w*|ped\w*)\b"),
)


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9? ]+", " ", text)
    return " ".join(text.split())


def is_purchase_list_query(message: str) -> bool:
    """True when the user asks for a replenishment list, not a single SKU."""
    msg = _normalize(message)
    if not msg:
        return False
    if msg.endswith("?"):
        msg = msg[:-1].strip()
    return any(pattern.search(msg) for pattern in PURCHASE_LIST_PATTERNS)
