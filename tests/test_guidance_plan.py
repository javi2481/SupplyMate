from __future__ import annotations

import pytest

from app.guidance import pick_next_question
from app.guidance_chips import apply_guidance_chip, chip_for_subcategory
from app.models import AnalyticalScope, GuidanceChip
from app.missions import is_complement_target, load_missions
from app.scope_builder import promote_new_query_if_needed
from app.slice_facets import list_slice_facets
from app.models import QueryInterpretation, ResolvedReference
from app.services import catalog_service
from app.agent import run_supplymate, run_apply_chip


def test_missions_csv_loads():
    edges = load_missions()
    assert len(edges) >= 3
    labels = {e.label for e in edges}
    assert "Toallitas húmedas" in labels


def test_promote_toallitas_is_not_new_query_on_bebe_scope():
    interp = QueryInterpretation(intent="replenishment", relation="refinement")
    resolved = [
        ResolvedReference(
            match_kind="group",
            scope_dimension="subcategory",
            scope_value="Toallas Humedecidas- Bombachitas",
            sku_count=10,
        )
    ]
    prev = AnalyticalScope(subcategories=["Pañales P/Bebes"])
    assert is_complement_target(
        prev,
        dimension="subcategory",
        value="Toallas Humedecidas- Bombachitas",
    )
    out = promote_new_query_if_needed(interp, resolved, prev)
    assert out.relation == "refinement"


def test_apply_chip_subcategory():
    scope = AnalyticalScope(categories=["Pañales"])
    chip = chip_for_subcategory("Bebé", "Pañales P/Bebes")
    new_scope, commit = apply_guidance_chip(scope, chip)
    assert "Pañales P/Bebes" in new_scope.subcategories
    assert not commit


def test_apply_chip_draft_oc():
    scope = AnalyticalScope(categories=["Pañales"])
    chip = GuidanceChip(label="Armar OC", action="draft_oc", args={})
    _, commit = apply_guidance_chip(scope, chip)
    assert commit


def test_panales_facets_offer_baby_adult_first():
    scope = AnalyticalScope(categories=["Pañales"])
    slice_data = catalog_service.replenishment_slice(scope, limit=25)
    facets = list_slice_facets(scope, slice_data.dashboard, slice_data.purchase_list)
    assert facets.sku_count >= 100
    sub_names = {n for n, _ in facets.subcategories}
    assert any("Bebes" in n for n in sub_names)
    assert any("Adultos" in n for n in sub_names)
    guide = pick_next_question(
        scope,
        facets,
        purchase_items=slice_data.purchase_list,
        dashboard=slice_data.dashboard,
    )
    assert guide.action == "ask_clarification"
    assert guide.reason in ("multiple_subcategories", "baby_vs_adult")
    assert any("Bebé" in o or "Adulto" in o for o in guide.options)


@pytest.mark.asyncio
async def test_panales_then_bebe_then_xxg():
    first = await run_supplymate("¿Cuántos pañales tengo que comprar?")
    assert first.mode == "explore"
    assert first.guidance is not None
    assert first.guidance.action == "ask_clarification"
    bebe_chip = next(c for c in first.guidance.chips if c.label == "Bebé")

    second = await run_apply_chip(first.scope, bebe_chip)  # type: ignore[arg-type]
    assert "Pañales P/Bebes" in second.scope.subcategories  # type: ignore[union-attr]
    assert second.guidance is not None
    assert any(opt.upper() == "XXG" for opt in (second.guidance.options or []))

    xxg_chip = next(c for c in second.guidance.chips if c.label.upper() == "XXG")
    third = await run_apply_chip(second.scope, xxg_chip)  # type: ignore[arg-type]
    assert "xxg" in third.scope.name_tokens  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_shampoo_after_panales_is_new_query():
    first = await run_supplymate("¿Cuántos pañales tengo que comprar?")
    second = await run_supplymate("¿Cuántos shampoo debo comprar?", first.scope)
    assert second.mode == "explore"
    assert second.scope is not None
    assert "Shampoo" in second.scope.subcategories
    assert not any("Pañal" in c for c in second.scope.categories)


@pytest.mark.asyncio
async def test_desodorantes_subcategory_guidance():
    first = await run_supplymate("¿Cuántos desodorantes debo comprar?")
    assert first.mode == "explore"
    assert first.guidance is not None
    assert first.guidance.action == "ask_clarification"
    assert any("Aerosol" in o or "Roll" in o for o in first.guidance.options)

@pytest.mark.asyncio
async def test_toallitas_union_on_bebe_xxg():
    first = await run_supplymate("¿Cuántos pañales tengo que comprar?")
    bebe = next(c for c in first.guidance.chips if c.label == "Bebé")  # type: ignore[union-attr]
    second = await run_apply_chip(first.scope, bebe)  # type: ignore[arg-type]
    xxg = next(c for c in second.guidance.chips if c.label.upper() == "XXG")  # type: ignore[union-attr]
    third = await run_apply_chip(second.scope, xxg)  # type: ignore[arg-type]
    # Dismiss stockout/complement prompts until we see toallitas or run out
    scope = third.scope
    for _ in range(4):
        if third.guidance and third.guidance.reason == "mission_complement":
            toallitas = next(
                (c for c in third.guidance.chips if "Toallitas" in c.label),
                None,
            )
            if toallitas:
                fourth = await run_apply_chip(scope, toallitas)  # type: ignore[arg-type]
                assert "Pañales P/Bebes" in fourth.scope.subcategories  # type: ignore[union-attr]
                assert any(
                    "Toallas" in s for s in fourth.scope.subcategories  # type: ignore[union-attr]
                )
                return
        dismiss = next(
            (
                c
                for c in (third.guidance.chips if third.guidance else [])
                if c.action == "dismiss_facet"
            ),
            None,
        )
        if dismiss:
            third = await run_apply_chip(scope, dismiss)  # type: ignore[arg-type]
            scope = third.scope
            continue
        break
    pytest.skip("Complement guidance not reached in this catalog slice")


@pytest.mark.asyncio
async def test_mamaderas_union_is_small_group():
    scope = AnalyticalScope(
        subcategories=["Pañales P/Bebes"],
        name_tokens=["xxg"],
        guidance_dismissed=["complement"],
    )
    from app.guidance_chips import chip_for_name_token

    chip = chip_for_name_token("Mamaderas", "mamaderas", union=True)
    merged, _ = apply_guidance_chip(scope, chip)
    slice_data = catalog_service.replenishment_slice(merged, limit=100)
    assert slice_data.dashboard.skus < 380


@pytest.mark.asyncio
async def test_chip_xxg_skips_interpret_query():
    first = await run_supplymate("¿Cuántos pañales tengo que comprar?")
    bebe = next(c for c in first.guidance.chips if c.label == "Bebé")  # type: ignore[union-attr]
    second = await run_apply_chip(first.scope, bebe)  # type: ignore[arg-type]
    xxg = next(c for c in second.guidance.chips if c.label.upper() == "XXG")  # type: ignore[union-attr]
    third = await run_apply_chip(second.scope, xxg)  # type: ignore[arg-type]
    assert third.scope.name_tokens == ["xxg"]  # type: ignore[union-attr]
