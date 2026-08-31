from __future__ import annotations

import re
import unicodedata
from collections import Counter

from app.models import QueryInterpretation, Reference, ResolvedReference
from app.products import NUMERIC_CODE_RE, message_looks_like_sku, resolve_product_id
from app.replenishment import calculate_replenishment
from app.store import get_store

_QUERY_STOPWORDS = {
    "cuanto",
    "cuanta",
    "cuantos",
    "cuantas",
    "debo",
    "deberia",
    "debería",
    "tengo",
    "necesito",
    "hay",
    "que",
    "qué",
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
    "comprar",
    "compro",
    "compra",
    "pedir",
    "pido",
    "pedido",
    "reponer",
    "repongo",
    "reabastecer",
    "producto",
    "productos",
}


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def _stem(token: str) -> str:
    if len(token) > 4 and token.endswith("es"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def _token_matches_name(token: str, name: str) -> bool:
    if not token or not name:
        return False
    stem = _stem(token)
    if len(stem) < 3:
        return False
    if stem in name or token in name:
        return True
    for part in name.split():
        if len(part) < 3:
            continue
        if stem == _stem(part) or part in token or token in part:
            return True
    return False


def _qty_for_skus(sku_ids: list[str]) -> int:
    store = get_store()
    total = 0
    for pid in sku_ids:
        master = store.get_master(pid)
        calc = calculate_replenishment(
            product_id=master.product_id,
            current_stock=master.current_stock,
            total_units_sold_last_30=master.units_sold_30d,
            lead_time_days=master.lead_time_days,
            safety_stock=master.safety_stock,
        )
        total += calc.recommended_quantity
    return total


def _match_score(token: str, label: str) -> int:
    label_norm = normalize_text(label)
    if not label_norm:
        return 0
    if token == label_norm:
        return 100
    stem = _stem(token)
    if stem and stem == label_norm:
        return 95
    if label_norm.startswith(stem) or stem in label_norm.split():
        return 80
    if _token_matches_name(token, label_norm):
        return 60
    return 0


def _label_for_group(scope_dimension: str, scope_value: str) -> str:
    if scope_dimension == "subcategory":
        return scope_value
    return scope_value


def _pick_best_group(
    token: str,
    categories: dict[str, list[str]],
    subcategories: dict[str, list[str]],
) -> tuple[str, str, list[str]] | None:
    candidates: list[tuple[int, int, str, str, list[str]]] = []
    for cat, pids in categories.items():
        if len(pids) < 2:
            continue
        score = _match_score(token, cat)
        if score >= 60:
            candidates.append((score, len(pids), "category", cat, pids))
    for sub, pids in subcategories.items():
        if len(pids) < 2:
            continue
        score = _match_score(token, sub)
        if score >= 60:
            candidates.append((score, len(pids), "subcategory", sub, pids))

    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], -item[1], item[3]))
    best = candidates[0]

    cat_candidates = [c for c in candidates if c[2] == "category"]
    sub_candidates = [c for c in candidates if c[2] == "subcategory"]
    if len(cat_candidates) > 1:
        top_score = cat_candidates[0][0]
        tied_cats = [c for c in cat_candidates if c[0] >= top_score - 5]
        if len(tied_cats) > 1:
            return None
    if cat_candidates and sub_candidates:
        best_cat = cat_candidates[0]
        best_sub = sub_candidates[0]
        if best_cat[0] >= 60 and best_cat[1] >= best_sub[1]:
            return best_cat[2], best_cat[3], best_cat[4]
        if best_sub[0] >= 95 and best_sub[0] > best_cat[0] + 10:
            return best_sub[2], best_sub[3], best_sub[4]

    if len(candidates) > 1:
        second = candidates[1]
        if best[0] == second[0] and abs(best[1] - second[1]) < 5:
            if cat_candidates and len(cat_candidates) == 1:
                chosen = cat_candidates[0]
                return chosen[2], chosen[3], chosen[4]
            return None
        if best[0] - second[0] < 15 and second[0] >= 80:
            if cat_candidates and len(cat_candidates) == 1 and best[2] != "category":
                chosen = cat_candidates[0]
                if chosen[1] >= second[1]:
                    return chosen[2], chosen[3], chosen[4]
            return None
    return best[2], best[3], best[4]


def resolve_single_reference(ref: Reference) -> ResolvedReference:
    raw = ref.text.strip()
    user_text = raw
    store = get_store()

    if ref.kind == "sku_hint" or NUMERIC_CODE_RE.fullmatch(raw):
        try:
            product_id = resolve_product_id(raw)
            master = store.get_master(product_id)
            qty = calculate_replenishment(
                product_id=master.product_id,
                current_stock=master.current_stock,
                total_units_sold_last_30=master.units_sold_30d,
                lead_time_days=master.lead_time_days,
                safety_stock=master.safety_stock,
            ).recommended_quantity
            return ResolvedReference(
                label=master.product_name,
                user_text=user_text,
                match_kind="exact_sku",
                product_id=product_id,
                sku_ids=[product_id],
                scope_dimension="sku_set",
                scope_value=product_id,
                sku_count=1,
                recommended_quantity=qty,
                confidence="high",
            )
        except Exception:
            return ResolvedReference(
                user_text=user_text,
                match_kind="unresolved",
                confidence="low",
            )

    token = normalize_text(raw)
    if not token:
        return ResolvedReference(user_text=user_text, match_kind="unresolved")

    categories: dict[str, list[str]] = {}
    subcategories: dict[str, list[str]] = {}
    name_hits: list[str] = []

    for master in store.products.values():
        pid = master.product_id
        cat = (master.category or "").strip()
        sub = (master.subcategory or "").strip()
        name_norm = normalize_text(master.product_name)

        if _token_matches_name(token, normalize_text(cat)):
            categories.setdefault(cat, []).append(pid)
        if sub and _token_matches_name(token, normalize_text(sub)):
            subcategories.setdefault(sub, []).append(pid)
        if _token_matches_name(token, name_norm) or token in name_norm:
            name_hits.append(pid)

    name_hits = list(dict.fromkeys(name_hits))

    if len(name_hits) == 1:
        pid = name_hits[0]
        master = store.get_master(pid)
        qty = calculate_replenishment(
            product_id=master.product_id,
            current_stock=master.current_stock,
            total_units_sold_last_30=master.units_sold_30d,
            lead_time_days=master.lead_time_days,
            safety_stock=master.safety_stock,
        ).recommended_quantity
        return ResolvedReference(
            label=master.product_name,
            user_text=user_text,
            match_kind="exact_sku",
            product_id=pid,
            sku_ids=[pid],
            scope_dimension="sku_set",
            scope_value=pid,
            sku_count=1,
            recommended_quantity=qty,
            confidence="high",
        )

    group_pick = _pick_best_group(token, categories, subcategories)
    if group_pick:
        dim, value, pids = group_pick
        return ResolvedReference(
            label=_label_for_group(dim, value),
            user_text=user_text,
            match_kind="group",
            sku_ids=pids,
            scope_dimension=dim,  # type: ignore[arg-type]
            scope_value=value,
            sku_count=len(pids),
            recommended_quantity=_qty_for_skus(pids),
            confidence="high",
        )

    group_candidates: list[tuple[str, str, list[str]]] = []
    for cat, pids in categories.items():
        if len(pids) >= 2:
            group_candidates.append(("category", cat, pids))
    for sub, pids in subcategories.items():
        if len(pids) >= 2:
            group_candidates.append(("subcategory", sub, pids))

    if len(group_candidates) == 1:
        dim, value, pids = group_candidates[0]
        return ResolvedReference(
            label=_label_for_group(dim, value),
            user_text=user_text,
            match_kind="group",
            sku_ids=pids,
            scope_dimension=dim,  # type: ignore[arg-type]
            scope_value=value,
            sku_count=len(pids),
            recommended_quantity=_qty_for_skus(pids),
            confidence="high",
        )

    if len(group_candidates) > 1:
        options = [f"{dim}: {val}" for dim, val, _ in group_candidates[:5]]
        return ResolvedReference(
            user_text=user_text,
            match_kind="ambiguous",
            confidence="low",
        )

    if len(name_hits) >= 2:
        cats = Counter(store.get_master(p).category for p in name_hits)
        if len(cats) == 1:
            cat = next(iter(cats))
            return ResolvedReference(
                label=cat,
                user_text=user_text,
                match_kind="group",
                sku_ids=name_hits,
                scope_dimension="category",
                scope_value=cat,
                sku_count=len(name_hits),
                recommended_quantity=_qty_for_skus(name_hits),
                confidence="high",
            )
        return ResolvedReference(
            user_text=user_text,
            match_kind="ambiguous",
            confidence="low",
        )

    return ResolvedReference(user_text=user_text, match_kind="unresolved", confidence="low")


def resolve_references(interpretation: QueryInterpretation) -> list[ResolvedReference]:
    if not interpretation.references:
        return []
    return [resolve_single_reference(ref) for ref in interpretation.references]


def disambiguation_options(resolved: list[ResolvedReference]) -> list[str]:
    options: list[str] = []
    for item in resolved:
        if item.match_kind == "ambiguous":
            token = normalize_text(item.user_text)
            store = get_store()
            seen: set[str] = set()
            for master in store.products.values():
                cat = (master.category or "").strip()
                sub = (master.subcategory or "").strip()
                if cat and _token_matches_name(token, normalize_text(cat)) and cat not in seen:
                    seen.add(cat)
                    options.append(cat)
                if sub and _token_matches_name(token, normalize_text(sub)) and sub not in seen:
                    seen.add(sub)
                    options.append(sub)
    return options[:5]
