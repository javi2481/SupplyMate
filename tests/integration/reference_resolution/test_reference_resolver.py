from collections import Counter, defaultdict
from functools import lru_cache

import pytest

from app.catalog.store import get_store
from app.core.models import Reference
from app.pipeline.query_interpretation import interpret_query_rules
from app.pipeline.reference_resolver import (
    FAMILY_CONTAINMENT,
    MIN_GROUP_SCORE,
    SCORE_PREFIX_OR_TOKEN,
    _collect_entity_indexes,
    _family_from_name_hits,
    _match_score,
    _supplier_match_score,
    _token_matches_name,
    normalize_text,
    resolve_single_reference,
)


def test_jabones_group_has_many_skus():
    resolved = resolve_single_reference(Reference(text="jabones"))
    assert resolved.match_kind == "group"
    assert resolved.sku_count >= 10
    assert resolved.recommended_quantity > 0


def test_shampoo_is_subcategory():
    resolved = resolve_single_reference(Reference(text="shampoo"))
    assert resolved.match_kind == "group"
    assert resolved.scope_dimension == "subcategory"
    assert "Shampoo" in resolved.scope_value


def test_interpret_jabones_purchase():
    interp = interpret_query_rules("¿Cuántos jabones debo comprar?")
    assert interp is not None
    assert interp.intent == "replenishment"
    assert any(r.text == "jabones" for r in interp.references)


def test_interpret_jabones_and_shampoo():
    interp = interpret_query_rules("¿Cuántos jabones y shampoo debo comprar?")
    assert interp is not None
    texts = {r.text for r in interp.references}
    assert "jabones" in texts
    assert "shampoo" in texts


def test_interpret_inventory_risk():
    interp = interpret_query_rules("¿Qué jabones tienen riesgo?")
    assert interp is not None
    assert interp.intent == "inventory_risk"


def test_interpret_me_refiero_panales_xxg():
    interp = interpret_query_rules("me refiero a pañales xxg")
    assert interp is not None
    assert interp.intent == "replenishment"
    texts = " ".join(r.text for r in interp.references)
    assert "panales" in texts or "pañales" in texts
    assert "xxg" in texts


def test_xxg_does_not_match_xxxg():
    resolved = resolve_single_reference(Reference(text="xxg"))
    assert resolved.match_kind == "group"
    assert "xxg" in resolved.name_tokens
    from app.catalog.store import get_store

    store = get_store()
    assert resolved.sku_ids
    for pid in resolved.sku_ids:
        parts = set(store.get_master(pid).product_name.lower().split())
        assert "xxg" in parts
        assert "xxxg" not in parts


def test_panales_xxg_keeps_category_and_size():
    resolved = resolve_single_reference(Reference(text="pañales xxg"))
    assert resolved.match_kind == "group"
    assert resolved.scope_dimension == "category"
    assert "Pañal" in (resolved.scope_value or "")
    assert "xxg" in resolved.name_tokens
    assert resolved.sku_count >= 2
    from app.catalog.store import get_store

    store = get_store()
    for pid in resolved.sku_ids:
        parts = set(store.get_master(pid).product_name.lower().split())
        assert "xxg" in parts
        assert "xxxg" not in parts


def test_cosmetica_prefers_category_over_unique_name_hit():
    """«cosmética» must not hijack to BASICCARE BOTELLAS COSMETICAS (8112743)."""
    resolved = resolve_single_reference(Reference(text="cosmética"))
    assert resolved.match_kind == "group"
    assert resolved.scope_dimension == "category"
    assert resolved.scope_value == "Cosmetica"
    assert resolved.product_id != "8112743"
    assert "8112743" not in resolved.sku_ids or resolved.sku_count > 1


def test_unilever_resolves_supplier_union():
    resolved = resolve_single_reference(Reference(text="unilever", kind="product_group"))
    assert resolved.match_kind == "group"
    assert resolved.scope_dimension == "supplier"
    assert "UNILEVER" in resolved.scope_value
    assert "UNILEVER" in resolved.scope_values
    assert "UNILEVER (HOME CARE)" in resolved.scope_values
    assert resolved.sku_count >= 400


def test_loreal_prefers_supplier_over_name_token():
    resolved = resolve_single_reference(Reference(text="loreal", kind="product_group"))
    assert resolved.match_kind == "group"
    assert resolved.scope_dimension == "supplier"
    assert "LOREAL" in resolved.scope_value.upper()
    # Name-token proxy was ~181; supplier coverage is ~1000.
    assert resolved.sku_count >= 500
    assert not resolved.name_tokens


def test_cosmetica_prefers_category_over_supplier_collision():
    resolved = resolve_single_reference(Reference(text="cosmetica", kind="product_group"))
    assert resolved.match_kind == "group"
    assert resolved.scope_dimension == "category"
    assert resolved.scope_value == "Cosmetica"


def test_desodorante_singular_resolves_category():
    resolved = resolve_single_reference(Reference(text="desodorante", kind="product_group"))
    assert resolved.match_kind == "group"
    assert resolved.scope_dimension == "category"
    assert "Desodorante" in resolved.scope_value
    assert resolved.sku_count >= 100


def test_build_scope_applies_supplier_values():
    from app.core.models import QueryInterpretation
    from app.pipeline.scope_builder import build_scope

    resolved = resolve_single_reference(Reference(text="unilever", kind="product_group"))
    scope = build_scope(
        QueryInterpretation(intent="inventory_risk", references=[Reference(text="unilever")]),
        [resolved],
    )
    assert "UNILEVER" in scope.suppliers
    assert "UNILEVER (HOME CARE)" in scope.suppliers


def test_sin_stock_rules_have_hint_no_junk_ref():
    from app.pipeline.query_interpretation import enrich_interpretation_from_message

    interp = interpret_query_rules("productos sin stock")
    assert interp is not None
    interp = enrich_interpretation_from_message(interp, "productos sin stock")
    assert interp.intent == "inventory_risk"
    assert "sin stock" in interp.filter_hints
    assert interp.references == []


def test_me_falta_de_unilever_rules():
    from app.pipeline.query_interpretation import enrich_interpretation_from_message

    msg = "que me falta de unilever?"
    interp = interpret_query_rules(msg)
    assert interp is not None
    interp = enrich_interpretation_from_message(interp, msg)
    assert interp.intent == "inventory_risk"
    assert "me falta" in interp.filter_hints
    assert any(r.text.lower() == "unilever" for r in interp.references)
    assert not any("falta" in r.text.lower() and r.text.lower() != "unilever" for r in interp.references)


# --------------------------------------------------------------------------
# Family containment: a taxonomy node that matches the token and holds its name
# hits beats the raw hit set. Cases are selected from the live store by shape,
# so a catalog rename changes which token is exercised, not whether it passes.
# --------------------------------------------------------------------------

MIN_TOKEN_LEN = 4
MAX_SHAPE_CASES = 5


@lru_cache(maxsize=1)
def _catalog_shape() -> tuple[dict[str, frozenset[str]], dict[str, frozenset[str]], dict[str, frozenset[str]]]:
    """Name-token → SKUs, plus SKUs per category and per subcategory label."""
    store = get_store()
    by_token: dict[str, set[str]] = defaultdict(set)
    by_category: dict[str, set[str]] = defaultdict(set)
    by_subcategory: dict[str, set[str]] = defaultdict(set)
    for master in store.products.values():
        pid = master.product_id
        for word in set(normalize_text(master.product_name).split()):
            if len(word) >= MIN_TOKEN_LEN:
                by_token[word].add(pid)
        if (master.category or "").strip():
            by_category[master.category.strip()].add(pid)
        if (master.subcategory or "").strip():
            by_subcategory[master.subcategory.strip()].add(pid)
    return (
        {t: frozenset(p) for t, p in by_token.items() if len(p) >= 2},
        {c: frozenset(p) for c, p in by_category.items()},
        {s: frozenset(p) for s, p in by_subcategory.items()},
    )


def _name_hits(token: str) -> frozenset[str]:
    """The hits the resolver itself would see (stem rule, not literal words)."""
    return frozenset(_collect_entity_indexes(token)[3])


@lru_cache(maxsize=1)
def _family_shape_tokens() -> tuple[tuple[str, frozenset[str], str, str], ...]:
    """Tokens whose name hits all sit inside one node whose label matches them."""
    by_token, by_category, by_subcategory = _catalog_shape()
    labels = [lab for lab in list(by_category) + list(by_subcategory) if lab]
    cases: list[tuple[str, frozenset[str], str, str]] = []
    for token in sorted(by_token, key=lambda t: (-len(by_token[t]), t)):
        matching = [lab for lab in labels if _match_score(token, lab) >= MIN_GROUP_SCORE]
        if not matching:
            continue
        hits = _name_hits(token)
        if len(hits) < 2:
            continue
        for dim, index in (("subcategory", by_subcategory), ("category", by_category)):
            contained = [lab for lab in matching if lab in index and hits <= index[lab]]
            if len(contained) == 1:
                cases.append((token, hits, dim, contained[0]))
                break
        if len(cases) >= MAX_SHAPE_CASES:
            break
    return tuple(cases)


@lru_cache(maxsize=1)
def _cross_node_shape_tokens() -> tuple[tuple[str, frozenset[str]], ...]:
    """Tokens matching names across >=2 nodes at both levels and no node label."""
    by_token, by_category, by_subcategory = _catalog_shape()
    labels = [lab for lab in list(by_category) + list(by_subcategory) if lab]
    store = get_store()
    supplier_labels = {
        (master.supplier or "").strip()
        for master in store.products.values()
        if (master.supplier or "").strip()
    }
    cases: list[tuple[str, frozenset[str]]] = []
    for token in sorted(by_token, key=lambda t: (-len(by_token[t]), t)):
        if any(_match_score(token, lab) >= MIN_GROUP_SCORE for lab in labels):
            continue
        if any(
            _supplier_match_score(token, lab) >= SCORE_PREFIX_OR_TOKEN
            for lab in supplier_labels
        ):
            continue
        hits = _name_hits(token)
        if len(hits) < 2:
            continue
        masters = [store.get_master(pid) for pid in hits]
        spread_cat = Counter((m.category or "").strip() for m in masters)
        spread_sub = Counter((m.subcategory or "").strip() for m in masters)
        top = max(
            spread_cat.most_common(1)[0][1] if spread_cat else 0,
            spread_sub.most_common(1)[0][1] if spread_sub else 0,
        )
        if len(spread_cat) < 2 or len(spread_sub) < 2:
            continue
        if top / len(hits) >= FAMILY_CONTAINMENT:
            continue
        cases.append((token, hits))
        if len(cases) >= MAX_SHAPE_CASES:
            break
    return tuple(cases)


def test_catalog_offers_a_family_shaped_token():
    assert _family_shape_tokens(), (
        "no live token has name hits fully contained in a node whose label "
        "matches it — the family policy has nothing to assert against"
    )


def test_family_from_name_hits_promotes_the_containing_node():
    """The policy itself: label match plus containment yields the taxonomy node."""
    for token, hits, dim, label in _family_shape_tokens():
        categories, subcategories, _suppliers, name_hits = _collect_entity_indexes(token)
        promoted = _family_from_name_hits(token, token, name_hits, categories, subcategories)
        assert promoted is not None, f"{token!r} should promote to {dim} {label!r}"
        assert promoted.match_kind == "group"
        assert promoted.scope_dimension == dim
        assert promoted.scope_value == label
        assert promoted.sku_count >= len(hits)
        assert hits <= set(promoted.sku_ids)
        assert token in promoted.name_tokens


def test_family_beats_name_hits_end_to_end():
    """Resolution of a family-shaped token is the node, never a bare SKU set."""
    for token, hits, _dim, _label in _family_shape_tokens():
        resolved = resolve_single_reference(Reference(text=token))
        assert resolved.match_kind == "group", token
        assert resolved.scope_dimension in ("category", "subcategory"), token
        assert resolved.scope_dimension != "sku_set", token
        assert hits <= set(resolved.sku_ids), token
        assert resolved.sku_count >= len(hits), token


def test_containment_alone_does_not_promote():
    """Triangulation: hits spread over >=2 nodes with no matching label stay a SKU set."""
    cases = _cross_node_shape_tokens()
    assert cases, "no live token has the cross-node attribute shape"
    for token, hits in cases:
        resolved = resolve_single_reference(Reference(text=token))
        assert resolved.scope_dimension == "sku_set", token
        assert token in resolved.name_tokens, token
        assert set(resolved.sku_ids) == set(hits), token


def test_conjunction_applies_the_same_family_policy():
    """A multi-token reference contained in a matching node resolves to that node."""
    _by_token, by_category, by_subcategory = _catalog_shape()
    store = get_store()
    checked = 0
    for token, _hits, _dim, _label in _family_shape_tokens():
        companions = Counter()
        for pid in _name_hits(token):
            for word in set(normalize_text(store.get_master(pid).product_name).split()):
                if len(word) >= MIN_TOKEN_LEN and word != token:
                    companions[word] += 1
        for other, count in companions.most_common(3):
            if count < 2:
                continue
            resolved = resolve_single_reference(Reference(text=f"{token} {other}"))
            if resolved.match_kind != "group" or resolved.sku_count < 2:
                continue
            checked += 1
            pids = set(resolved.sku_ids)
            for index in (by_subcategory, by_category):
                contained = [
                    lab
                    for lab, members in index.items()
                    if lab
                    and _match_score(token, lab) >= MIN_GROUP_SCORE
                    and len(pids & members) >= len(pids) * FAMILY_CONTAINMENT
                ]
                if contained:
                    assert resolved.scope_dimension != "sku_set", f"{token} {other}"
                    break
    assert checked, "no shape-built conjunction was resolvable"


@pytest.mark.parametrize("size_token", ["xxg", "xxxg"])
def test_size_token_never_promotes_to_a_family(size_token):
    """The size trap: an attribute token keeps its exact-name SKU set."""
    resolved = resolve_single_reference(Reference(text=size_token))
    assert resolved.match_kind == "group"
    assert resolved.scope_dimension == "sku_set"
    assert size_token in resolved.name_tokens
    store = get_store()
    for pid in resolved.sku_ids:
        assert _token_matches_name(
            size_token, normalize_text(store.get_master(pid).product_name)
        )