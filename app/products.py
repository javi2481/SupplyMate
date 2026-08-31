from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from app.intents import is_purchase_list_query, is_top_categories_query
from app.models import ProductNotFoundError
from app.store import get_store, reset_store_cache

NUMERIC_CODE_RE = re.compile(r"\d{5,}")

STOPWORDS = {
    "cuanto",
    "cuánta",
    "cuanta",
    "deberia",
    "debería",
    "pedir",
    "pedido",
    "producto",
    "product",
    "prod",
    "del",
    "de",
    "la",
    "el",
    "los",
    "las",
    "un",
    "una",
    "para",
    "por",
    "que",
    "qué",
    "recomendacion",
    "recomendación",
    "reabastecer",
    "stock",
    "necesito",
    "quiero",
}


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def load_products(products_csv: Path | None = None) -> list[dict[str, str]]:
    _ = products_csv
    return get_store().list_products()


def _lexical_resolve(query: str, products: list[dict[str, str]]) -> str | None:
    q = _normalize(query)
    if not q:
        return None
    scored: list[tuple[int, str]] = []
    for row in products:
        pid = row["product_id"]
        name = _normalize(row["product_name"])
        score = 0
        if q == name:
            score = 100
        elif q and q in name:
            score = 80 + min(len(q), 15)
        elif name and name in q:
            score = 70 + min(len(name), 15)
        else:
            tokens = [t for t in name.split() if len(t) >= 4 and t not in STOPWORDS]
            hits = sum(1 for t in tokens if t in q.split() or t in q)
            if tokens and hits:
                score = 40 + 20 * hits
        if score:
            scored.append((score, pid))
    if not scored:
        return None
    scored.sort(key=lambda item: (-item[0], item[1]))
    best_score, best_id = scored[0]
    tied = [pid for score, pid in scored if score == best_score]
    if len(tied) > 1 and best_score < 70:
        return None
    return best_id


def resolve_product_id(
    query: str,
    products_csv: Path | None = None,
) -> str:
    """Resolve free-text to product_id: catalog code, barcode, or name."""
    _ = products_csv
    store = get_store()
    products = store.list_products()
    if not products:
        raise ProductNotFoundError(query)

    raw = query.strip()

    exact = store.resolve_exact(raw)
    if exact:
        return exact

    for match in NUMERIC_CODE_RE.finditer(raw):
        found = store.resolve_exact(match.group(0))
        if found:
            return found

    if re.fullmatch(r"\d+", raw):
        found = store.resolve_exact(raw)
        if found:
            return found
        raise ProductNotFoundError(query)

    lexical = _lexical_resolve(raw, products)
    if lexical:
        return lexical

    raise ProductNotFoundError(query)


def message_looks_like_sku(message: str) -> bool:
    """True when the text contains a catalog-style numeric code (5+ digits)."""
    return bool(NUMERIC_CODE_RE.search(message or ""))


def resolve_from_message(message: str, products_csv: Path | None = None) -> str | None:
    """Extract a product reference from a natural-language message."""
    _ = products_csv
    if is_purchase_list_query(message) or is_top_categories_query(message):
        return None

    store = get_store()

    for match in NUMERIC_CODE_RE.finditer(message):
        found = store.resolve_exact(match.group(0))
        if found:
            return found

    msg = _normalize(message)
    products = store.list_products()
    lexical = _lexical_resolve(msg, products)
    if lexical:
        name = next(
            (
                _normalize(row["product_name"])
                for row in store.list_products()
                if row["product_id"] == lexical
            ),
            "",
        )
        tokens = [t for t in name.split() if len(t) >= 4 and t not in STOPWORDS]
        if name in msg or any(t in msg for t in tokens):
            return lexical

    residual = " ".join(t for t in msg.split() if t not in STOPWORDS)
    if residual:
        try:
            return resolve_product_id(residual)
        except ProductNotFoundError:
            pass

    return None


def clear_product_caches() -> None:
    reset_store_cache()
