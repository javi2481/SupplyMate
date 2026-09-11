from app.core.models import Reference
from app.pipeline.query_interpretation import interpret_query_rules
from app.pipeline.reference_resolver import resolve_single_reference


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