from app.models import AnalyticalScope, Reference
from app.query_interpretation import classify_relation, interpret_query_rules
from app.reference_resolver import resolve_single_reference
from app.scope_builder import build_scope, promote_new_query_if_needed
from app.agent import run_supplymate
import pytest


def test_classify_xxg_as_refinement_when_scope_exists():
    previous = AnalyticalScope(categories=["Pañales"])
    assert classify_relation("Me refiero a los XXG", previous) == "refinement"
    assert classify_relation("XXG", previous) == "refinement"
    assert classify_relation("los XXG", previous) == "refinement"


def test_classify_shampoo_as_new_query_even_with_scope():
    previous = AnalyticalScope(categories=["Pañales"])
    assert classify_relation("¿Cuántos shampoo debo comprar?", previous) == "new_query"


def test_interpret_me_refiero_xxg():
    interp = interpret_query_rules(
        "me refiero a los XXG",
        AnalyticalScope(categories=["Pañales"]),
    )
    assert interp is not None
    assert interp.intent == "replenishment"
    assert interp.relation == "refinement"
    assert any("xxg" in r.text.lower() for r in interp.references)


def test_xxg_name_token_not_xxxg():
    resolved = resolve_single_reference(Reference(text="xxg"))
    assert resolved.match_kind == "group"
    assert "xxg" in resolved.name_tokens
    from app.store import get_store

    store = get_store()
    for pid in resolved.sku_ids:
        parts = set(store.get_master(pid).product_name.lower().split())
        assert "xxg" in parts
        assert "xxxg" not in parts


def test_build_scope_refinement_keeps_category():
    previous = AnalyticalScope(categories=["Pañales"])
    from app.models import QueryInterpretation, ResolvedReference

    interp = QueryInterpretation(intent="replenishment", relation="refinement")
    resolved = [
        ResolvedReference(
            match_kind="group",
            scope_dimension="sku_set",
            name_tokens=["xxg"],
            sku_count=10,
        )
    ]
    scope = build_scope(interp, resolved, previous)
    assert "Pañales" in scope.categories
    assert "xxg" in scope.name_tokens


def test_promote_shampoo_followup_to_new_query():
    from app.models import QueryInterpretation, ResolvedReference

    interp = QueryInterpretation(intent="replenishment", relation="refinement")
    resolved = [
        ResolvedReference(
            match_kind="group",
            scope_dimension="subcategory",
            scope_value="Shampoo",
            sku_count=10,
        )
    ]
    out = promote_new_query_if_needed(
        interp, resolved, AnalyticalScope(categories=["Pañales"])
    )
    assert out.relation == "new_query"


@pytest.mark.asyncio
async def test_panales_then_xxg_keeps_category_and_guides():
    first = await run_supplymate("¿Cuántos pañales tengo que comprar?")
    assert first.mode == "explore"
    assert first.scope is not None
    assert any("Pañal" in c for c in first.scope.categories)
    assert first.guidance is not None
    assert first.guidance.action == "ask_clarification"
    assert any(opt == "Bebé" for opt in first.guidance.options)

    from app.agent import run_apply_chip

    bebe_chip = next(c for c in first.guidance.chips if c.label == "Bebé")
    scoped = await run_apply_chip(first.scope, bebe_chip)
    assert scoped.scope is not None
    assert "Pañales P/Bebes" in scoped.scope.subcategories

    second = await run_supplymate("Me refiero a los XXG", scoped.scope)
    assert second.mode == "explore"
    assert second.scope is not None
    assert any("Pañal" in c for c in second.scope.categories)
    assert "xxg" in second.scope.name_tokens
    assert second.dashboard is not None
    assert first.dashboard is not None
    assert 0 < second.dashboard.skus < first.dashboard.skus
    names = [i.product_name.lower() for i in second.purchase_list]
    if names:
        assert all("xxg" in n.split() for n in names)
        assert all("xxxg" not in n.split() for n in names)
    assert "Perfecto" in second.answer


@pytest.mark.asyncio
async def test_shampoo_after_panales_is_new_query():
    first = await run_supplymate("¿Cuántos pañales tengo que comprar?")
    second = await run_supplymate("¿Cuántos shampoo debo comprar?", first.scope)
    assert second.mode == "explore"
    assert second.scope is not None
    assert "Shampoo" in second.scope.subcategories
    assert not any("Pañal" in c for c in second.scope.categories)
    assert not second.scope.name_tokens
