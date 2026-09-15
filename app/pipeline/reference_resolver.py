from __future__ import annotations

import re
import unicodedata
from typing import Literal

from app.catalog.products import NUMERIC_CODE_RE, resolve_product_id
from app.catalog.store import get_store
from app.core.models import QueryInterpretation, Reference, ResolvedReference
from app.core.replenishment import calculate_replenishment

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
    "refiero",
    "referia",
    "refería",
    "solo",
    "solamente",
    "talle",
    "talla",
}


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


SIZE_TOKEN_RE = re.compile(r"^x{1,3}g$")


def _stem(token: str) -> str:
    if len(token) > 4 and token.endswith("es"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def _token_matches_name(token: str, name: str) -> bool:
    if not token or not name:
        return False
    parts = name.split()
    for piece in token.split():
        stem = _stem(piece)
        if len(stem) < 3:
            return False
        matched = False
        for part in parts:
            if len(part) < 3:
                continue
            if piece == part or stem == _stem(part):
                matched = True
                break
        if not matched:
            return False
    return True


def name_has_token(product_name: str, token: str) -> bool:
    """Whole-word match so 'xxg' does not hit 'xxxg'."""
    return _token_matches_name(normalize_text(token), normalize_text(product_name))


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


# Match-score ladder used by _match_score / _pick_best_group (higher = tighter).
SCORE_EXACT = 100
SCORE_STEM = 95
SCORE_PREFIX_OR_TOKEN = 80
SCORE_NAME_MATCH = 60

# Tie-break policy for group resolution (prefer None/ambiguity over a weak guess).
MIN_GROUP_SCORE = SCORE_NAME_MATCH
CATEGORY_TIE_SCORE_DELTA = 5
CLOSE_SECOND_SCORE_GAP = 15
MIN_CLOSE_SECOND_SCORE = SCORE_PREFIX_OR_TOKEN
SKU_COUNT_NEAR_TIE = 5
SUBCATEGORY_OVER_CATEGORY_MARGIN = 10

# Share of a token's name hits that must sit inside one taxonomy node before the
# node wins over the raw hit set.
FAMILY_CONTAINMENT = 0.9

# Vernacular stems that share a catalog taxonomy label (category/subcategory only).
# Example: users say «perfumes»; the catalog node is «Fragancias».
_TAXONOMY_ALIAS_STEM_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({"perfume", "fragancia"}),
)


def _taxonomy_alias_stems(token: str) -> frozenset[str]:
    stem = _stem(normalize_text(token))
    if len(stem) < 3:
        return frozenset({stem} if stem else ())
    for group in _TAXONOMY_ALIAS_STEM_GROUPS:
        if stem in group:
            return group
    return frozenset({stem})


def _taxonomy_alias_forms(token: str) -> list[str]:
    """Query forms for taxonomy scoring (token + vernacular aliases).

    `_stem` strips a trailing «es» aggressively («perfumes» → «perfum»), so we
    also try a simple singular «…s» and membership via prefix against alias stems.
    """
    norm = normalize_text(token)
    stem = _stem(norm)
    soft = norm[:-1] if len(norm) > 3 and norm.endswith("s") else norm
    forms = [token, norm, stem, soft]
    for group in _TAXONOMY_ALIAS_STEM_GROUPS:
        group_norms = {normalize_text(word) for word in group}
        group_stems = {_stem(word) for word in group_norms}
        linked = (
            stem in group_stems
            or soft in group_norms
            or soft in group_stems
            or norm in group_norms
            or any(
                len(stem) >= 5 and (member.startswith(stem) or stem.startswith(member))
                for member in group_stems
            )
        )
        if linked:
            forms.extend(group)
            forms.extend(group_norms)
            forms.extend(group_stems)
            break
    return list(dict.fromkeys(form for form in forms if len(form) >= 3))


def _taxonomy_match_score(token: str, label: str) -> int:
    """Score token against a taxonomy label, including vernacular aliases."""
    return max((_match_score(form, label) for form in _taxonomy_alias_forms(token)), default=0)


def _match_score(token: str, label: str) -> int:
    label_norm = normalize_text(label)
    if not label_norm:
        return 0
    if token == label_norm:
        return SCORE_EXACT
    stem = _stem(token)
    if stem and stem == label_norm:
        return SCORE_STEM
    if label_norm.startswith(stem) or stem in label_norm.split():
        return SCORE_PREFIX_OR_TOKEN
    if _token_matches_name(token, label_norm):
        return SCORE_NAME_MATCH
    return 0


def _label_for_group(scope_dimension: str, scope_value: str) -> str:
    if scope_dimension == "subcategory":
        return scope_value
    return scope_value


def _supplier_match_score(token: str, label: str) -> int:
    """Stricter than _match_score: ignore mid-label tokens (cuidado ≠ NEWSAN CUIDADO…)."""
    label_norm = normalize_text(label)
    if not label_norm or not token:
        return 0
    if token == label_norm:
        return SCORE_EXACT
    stem = _stem(token)
    first = label_norm.split()[0]
    if token == first:
        return SCORE_EXACT
    if stem and stem == _stem(first):
        return SCORE_STEM
    if label_norm.startswith(stem) or first.startswith(stem):
        return SCORE_PREFIX_OR_TOKEN
    return 0


def _index_label_hit(
    bucket: dict[str, list[str]],
    label: str,
    pid: str,
    token: str,
    *,
    min_score: int = MIN_GROUP_SCORE,
    score_fn=_match_score,
) -> None:
    label = (label or "").strip()
    if not label:
        return
    if score_fn(token, label) >= min_score:
        bucket.setdefault(label, []).append(pid)


def _supplier_family(token: str, labels: list[str]) -> bool:
    """True when every label shares the query stem as a prefix/first-token family."""
    stem = _stem(token)
    if len(stem) < 3:
        return False
    for label in labels:
        norm = normalize_text(label)
        if not norm:
            return False
        first = norm.split()[0]
        if norm.startswith(stem) or first.startswith(stem) or _stem(first) == stem:
            continue
        if token in norm.split():
            continue
        return False
    return True


def _pick_suppliers(
    token: str,
    suppliers: dict[str, list[str]],
) -> tuple[str, list[str], list[str]] | None | Literal["ambiguous"]:
    """Return (best_label, scope_values, sku_ids), None, or 'ambiguous'.

    Union related reasons sociales (UNILEVER + UNILEVER HOME CARE). Unrelated
    high-scoring suppliers → ambiguous. Requires score >= SCORE_PREFIX_OR_TOKEN.
    """
    candidates: list[tuple[int, int, str, list[str]]] = []
    for label, pids in suppliers.items():
        if not pids:
            continue
        score = _supplier_match_score(token, label)
        if score >= SCORE_PREFIX_OR_TOKEN:
            candidates.append((score, len(pids), label, pids))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], -item[1], item[2]))
    if len(candidates) == 1:
        score, _n, label, pids = candidates[0]
        return label, [label], list(dict.fromkeys(pids))

    labels = [c[2] for c in candidates]
    if _supplier_family(token, labels):
        all_pids: list[str] = []
        scope_values = [c[2] for c in candidates]
        for _s, _n, _lab, pids in candidates:
            all_pids.extend(pids)
        best_label = candidates[0][2]
        return best_label, scope_values, list(dict.fromkeys(all_pids))

    best, second = candidates[0], candidates[1]
    if best[0] - second[0] < CLOSE_SECOND_SCORE_GAP and second[0] >= MIN_CLOSE_SECOND_SCORE:
        return "ambiguous"
    label, pids = best[2], best[3]
    return label, [label], list(dict.fromkeys(pids))


def _pick_best_group(
    token: str,
    categories: dict[str, list[str]],
    subcategories: dict[str, list[str]],
) -> tuple[str, str, list[str]] | None:
    """Choose the best category/subcategory group for a token, or None if ambiguous.

    Policy:
    - Only consider groups scoring at least MIN_GROUP_SCORE (name-level match).
    - Prefer category over subcategory when the category is at least as large and
      scores well; take subcategory only when it is a near-exact stem match and
      clearly beats the category (SUBCATEGORY_OVER_CATEGORY_MARGIN).
    - If two categories are within CATEGORY_TIE_SCORE_DELTA, or the runner-up is
      within CLOSE_SECOND_SCORE_GAP with a high score (>= MIN_CLOSE_SECOND_SCORE),
      return None instead of guessing.
    """
    candidates: list[tuple[int, int, str, str, list[str]]] = []
    for cat, pids in categories.items():
        if len(pids) < 2:
            continue
        score = _taxonomy_match_score(token, cat)
        if score >= MIN_GROUP_SCORE:
            candidates.append((score, len(pids), "category", cat, pids))
    for sub, pids in subcategories.items():
        if len(pids) < 2:
            continue
        score = _taxonomy_match_score(token, sub)
        if score >= MIN_GROUP_SCORE:
            candidates.append((score, len(pids), "subcategory", sub, pids))

    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], -item[1], item[3]))
    best = candidates[0]

    cat_candidates = [c for c in candidates if c[2] == "category"]
    sub_candidates = [c for c in candidates if c[2] == "subcategory"]
    if len(cat_candidates) > 1:
        top_score = cat_candidates[0][0]
        tied_cats = [
            c for c in cat_candidates if c[0] >= top_score - CATEGORY_TIE_SCORE_DELTA
        ]
        if len(tied_cats) > 1:
            return None
    if cat_candidates and sub_candidates:
        best_cat = cat_candidates[0]
        best_sub = sub_candidates[0]
        if best_cat[0] >= MIN_GROUP_SCORE and best_cat[1] >= best_sub[1]:
            return best_cat[2], best_cat[3], best_cat[4]
        if (
            best_sub[0] >= SCORE_STEM
            and best_sub[0] > best_cat[0] + SUBCATEGORY_OVER_CATEGORY_MARGIN
        ):
            return best_sub[2], best_sub[3], best_sub[4]

    if len(candidates) > 1:
        second = candidates[1]
        if best[0] == second[0] and abs(best[1] - second[1]) < SKU_COUNT_NEAR_TIE:
            if cat_candidates and len(cat_candidates) == 1:
                chosen = cat_candidates[0]
                return chosen[2], chosen[3], chosen[4]
            return None
        if (
            best[0] - second[0] < CLOSE_SECOND_SCORE_GAP
            and second[0] >= MIN_CLOSE_SECOND_SCORE
        ):
            if cat_candidates and len(cat_candidates) == 1 and best[2] != "category":
                chosen = cat_candidates[0]
                if chosen[1] >= second[1]:
                    return chosen[2], chosen[3], chosen[4]
            return None
    return best[2], best[3], best[4]


def _resolved_supplier(
    user_text: str,
    best_label: str,
    scope_values: list[str],
    pids: list[str],
) -> ResolvedReference:
    return ResolvedReference(
        label=best_label,
        user_text=user_text,
        match_kind="group",
        sku_ids=pids,
        scope_dimension="supplier",
        scope_value=best_label,
        scope_values=scope_values,
        sku_count=len(pids),
        recommended_quantity=_qty_for_skus(pids),
        confidence="high",
    )


def _resolved_taxonomy(
    user_text: str,
    dim: str,
    value: str,
    pids: list[str],
) -> ResolvedReference:
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


def _display_token(token: str) -> str:
    if SIZE_TOKEN_RE.fullmatch(token):
        return token.upper()
    return token


def _product_matches_tokens(master, tokens: list[str]) -> bool:
    name_norm = normalize_text(master.product_name)
    cat_norm = normalize_text(master.category or "")
    sub_norm = normalize_text(master.subcategory or "")
    sup_norm = normalize_text(master.supplier or "")
    for piece in tokens:
        if _token_matches_name(piece, name_norm):
            continue
        if cat_norm and _token_matches_name(piece, cat_norm):
            continue
        if sub_norm and _token_matches_name(piece, sub_norm):
            continue
        if master.supplier and _supplier_match_score(piece, master.supplier) >= SCORE_PREFIX_OR_TOKEN:
            continue
        if sup_norm and _token_matches_name(piece, sup_norm):
            continue
        return False
    return True


def _group_from_name_hits(user_text: str, token: str, pids: list[str]) -> ResolvedReference:
    return ResolvedReference(
        label=_display_token(token),
        user_text=user_text,
        match_kind="group",
        sku_ids=pids,
        scope_dimension="sku_set",
        scope_value="",
        name_tokens=[token],
        sku_count=len(pids),
        recommended_quantity=_qty_for_skus(pids),
        confidence="high",
    )


def _family_from_name_hits(
    user_text: str,
    token: str,
    name_hits: list[str],
    categories: dict[str, list[str]],
    subcategories: dict[str, list[str]],
) -> ResolvedReference | None:
    """Return the taxonomy node the token's name hits live in, or None.

    `categories` / `subcategories` come from `_collect_entity_indexes`, so they
    already only hold nodes whose label matches the token. Label match and
    containment are both required: containment alone promotes any token, since
    almost every small hit set happens to sit inside some large node, and the
    promoted node would then swallow SKUs the token never named. Subcategory is
    tried before category so the tightest containing family wins.
    """
    hits = set(name_hits)
    if len(hits) < 2:
        return None
    needed = len(hits) * FAMILY_CONTAINMENT
    for dim, index in (("subcategory", subcategories), ("category", categories)):
        contained = [
            (label, pids)
            for label, pids in index.items()
            if len(pids) >= 2 and len(hits.intersection(pids)) >= needed
        ]
        if len(contained) != 1:
            continue
        label, pids = contained[0]
        resolved = _resolved_taxonomy(user_text, dim, label, list(dict.fromkeys(pids)))
        # The token stays a scope filter, so the recorte is the family narrowed
        # by the user's word: the dimension changes, the intent does not.
        return resolved.model_copy(update={"name_tokens": [token]})
    return None


def _collect_entity_indexes(token: str) -> tuple[
    dict[str, list[str]],
    dict[str, list[str]],
    dict[str, list[str]],
    list[str],
]:
    store = get_store()
    categories: dict[str, list[str]] = {}
    subcategories: dict[str, list[str]] = {}
    suppliers: dict[str, list[str]] = {}
    name_hits: list[str] = []

    for master in store.products.values():
        pid = master.product_id
        cat = (master.category or "").strip()
        sub = (master.subcategory or "").strip()
        supplier = (master.supplier or "").strip()
        name_norm = normalize_text(master.product_name)

        _index_label_hit(categories, cat, pid, token, score_fn=_taxonomy_match_score)
        _index_label_hit(subcategories, sub, pid, token, score_fn=_taxonomy_match_score)
        _index_label_hit(
            suppliers,
            supplier,
            pid,
            token,
            min_score=SCORE_PREFIX_OR_TOKEN,
            score_fn=_supplier_match_score,
        )
        if _token_matches_name(token, name_norm):
            name_hits.append(pid)

    return categories, subcategories, suppliers, list(dict.fromkeys(name_hits))


def _resolve_phrase_as_entity(user_text: str, phrase: str) -> ResolvedReference | None:
    """Resolve a full phrase against taxonomy then suppliers (before conjunction)."""
    categories, subcategories, suppliers, _name_hits = _collect_entity_indexes(phrase)
    group_pick = _pick_best_group(phrase, categories, subcategories)
    if group_pick:
        dim, value, pids = group_pick
        return _resolved_taxonomy(user_text, dim, value, pids)
    supplier_pick = _pick_suppliers(phrase, suppliers)
    if supplier_pick == "ambiguous":
        return ResolvedReference(
            user_text=user_text, match_kind="ambiguous", confidence="low"
        )
    if supplier_pick:
        best_label, scope_values, pids = supplier_pick
        return _resolved_supplier(user_text, best_label, scope_values, pids)
    return None


def _resolve_conjunction(user_text: str, tokens: list[str]) -> ResolvedReference:
    phrase = " ".join(tokens)
    phrase_hit = _resolve_phrase_as_entity(user_text, phrase)
    if phrase_hit is not None:
        return phrase_hit

    store = get_store()
    pids = [
        master.product_id
        for master in store.products.values()
        if _product_matches_tokens(master, tokens)
    ]
    pids = list(dict.fromkeys(pids))
    if not pids:
        return ResolvedReference(user_text=user_text, match_kind="unresolved", confidence="low")
    if len(pids) == 1:
        master = store.get_master(pids[0])
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
            product_id=pids[0],
            sku_ids=pids,
            scope_dimension="sku_set",
            scope_value=pids[0],
            sku_count=1,
            recommended_quantity=qty,
            confidence="high",
        )

    group_dim = ""
    group_val = ""
    name_tokens: list[str] = []
    for piece in tokens:
        cats: dict[str, list[str]] = {}
        subs: dict[str, list[str]] = {}
        for pid in pids:
            master = store.get_master(pid)
            cat = (master.category or "").strip()
            sub = (master.subcategory or "").strip()
            _index_label_hit(cats, cat, pid, piece, score_fn=_taxonomy_match_score)
            _index_label_hit(subs, sub, pid, piece, score_fn=_taxonomy_match_score)
        pick = _pick_best_group(piece, cats, subs)
        if pick and not group_val:
            group_dim, group_val, _ = pick
        elif not pick:
            name_tokens.append(piece)
            if not group_val:
                family = _family_from_name_hits(user_text, piece, pids, cats, subs)
                if family is not None:
                    group_dim, group_val = family.scope_dimension, family.scope_value

    label_parts: list[str] = []
    if group_val:
        label_parts.append(_label_for_group(group_dim, group_val))
    label_parts.extend(_display_token(t) for t in name_tokens)
    dim: str = group_dim if group_dim in ("category", "subcategory") else "sku_set"
    return ResolvedReference(
        label=" ".join(label_parts) or user_text,
        user_text=user_text,
        match_kind="group",
        sku_ids=pids,
        scope_dimension=dim,  # type: ignore[arg-type]
        scope_value=group_val,
        name_tokens=name_tokens,
        sku_count=len(pids),
        recommended_quantity=_qty_for_skus(pids),
        confidence="high",
    )


def resolve_single_reference(ref: Reference) -> ResolvedReference:
    raw = ref.text.strip()
    user_text = raw
    store = get_store()

    if ref.kind == "filter_hint":
        return ResolvedReference(
            user_text=user_text,
            match_kind="unresolved",
            confidence="low",
        )

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

    tokens = token.split()
    if len(tokens) > 1:
        return _resolve_conjunction(user_text, tokens)

    categories, subcategories, suppliers, name_hits = _collect_entity_indexes(token)

    # Prefer category/subcategory over supplier and over a unique product-name hit
    # so tokens like «cosmética» resolve to Cosmetica, not a supplier or SKU name.
    group_pick = _pick_best_group(token, categories, subcategories)
    if group_pick:
        dim, value, pids = group_pick
        return _resolved_taxonomy(user_text, dim, value, pids)

    supplier_pick = _pick_suppliers(token, suppliers)
    if supplier_pick == "ambiguous":
        return ResolvedReference(
            user_text=user_text, match_kind="ambiguous", confidence="low"
        )
    if supplier_pick:
        best_label, scope_values, pids = supplier_pick
        return _resolved_supplier(user_text, best_label, scope_values, pids)

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

    group_candidates: list[tuple[str, str, list[str]]] = []
    for cat, pids in categories.items():
        if len(pids) >= 2:
            group_candidates.append(("category", cat, pids))
    for sub, pids in subcategories.items():
        if len(pids) >= 2:
            group_candidates.append(("subcategory", sub, pids))

    if len(group_candidates) == 1:
        dim, value, pids = group_candidates[0]
        return _resolved_taxonomy(user_text, dim, value, pids)

    if len(group_candidates) > 1:
        return ResolvedReference(
            user_text=user_text,
            match_kind="ambiguous",
            confidence="low",
        )

    if len(name_hits) >= 2:
        family = _family_from_name_hits(
            user_text, token, name_hits, categories, subcategories
        )
        if family is not None:
            return family
        return _group_from_name_hits(user_text, token, name_hits)

    return ResolvedReference(user_text=user_text, match_kind="unresolved", confidence="low")


def resolve_references(interpretation: QueryInterpretation) -> list[ResolvedReference]:
    if not interpretation.references:
        return []
    return [
        resolve_single_reference(ref)
        for ref in interpretation.references
        if ref.kind != "filter_hint"
    ]


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
                if cat and _taxonomy_match_score(token, cat) >= MIN_GROUP_SCORE and cat not in seen:
                    seen.add(cat)
                    options.append(cat)
                if sub and _taxonomy_match_score(token, sub) >= MIN_GROUP_SCORE and sub not in seen:
                    seen.add(sub)
                    options.append(sub)
    return options[:5]
