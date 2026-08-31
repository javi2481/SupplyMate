import pytest

from app.models import ProductNotFoundError
from app.replenishment import calculate_replenishment
from app.services import catalog_service
from tests.catalog_ids import SKU_HIGH_QTY, SKU_UNKNOWN, SKU_ZERO_QTY


def test_get_master():
    master = catalog_service.get_master(SKU_HIGH_QTY)
    assert master.product_id == SKU_HIGH_QTY
    assert master.current_stock == 1
    assert master.units_sold_30d == 288


def test_search_products():
    hits = catalog_service.search_products("47 street", limit=3)
    assert hits
    assert any(h.product_id == SKU_ZERO_QTY for h in hits)


def test_replenishment_recommendation_high_qty():
    rec = catalog_service.get_replenishment_recommendation(SKU_HIGH_QTY)
    assert rec.recommended_quantity == 173


def test_replenishment_recommendation_zero_qty():
    rec = catalog_service.get_replenishment_recommendation(SKU_ZERO_QTY)
    assert rec.recommended_quantity == 0


def test_replenishment_unknown():
    with pytest.raises(ProductNotFoundError):
        catalog_service.get_replenishment_recommendation(SKU_UNKNOWN)


def test_recommendation_context_prices():
    rec = catalog_service.get_replenishment_recommendation(SKU_ZERO_QTY)
    assert rec.context.price is not None


def test_formula_parity():
    master = catalog_service.get_master(SKU_HIGH_QTY)
    calc = calculate_replenishment(
        product_id=master.product_id,
        current_stock=master.current_stock,
        total_units_sold_last_30=master.units_sold_30d,
        lead_time_days=master.lead_time_days,
        safety_stock=master.safety_stock,
    )
    rec = catalog_service.get_replenishment_recommendation(SKU_HIGH_QTY)
    assert rec.calculation.model_dump() == calc.model_dump()


def test_chat_dashboard_with_scope_reduces_skus():
    root_snap, _ = catalog_service.chat_dashboard(limit=25)
    assert root_snap.skus > 0
    first_category = root_snap.by_category[0].category if root_snap.by_category else ""
    if not first_category:
        pytest.skip("no categories in fixture data")
    from app.models import AnalyticalScope

    scoped_snap, scoped_items = catalog_service.chat_dashboard(
        limit=25,
        scope=AnalyticalScope(categories=[first_category]),
    )
    assert scoped_snap.skus <= root_snap.skus
    assert all(item.category == first_category or not item.category for item in scoped_items)


def test_replenishment_slice_empty_evidence():
    from app.models import AnalyticalScope

    slice_ = catalog_service.replenishment_slice(
        AnalyticalScope(categories=["__no_such_category__"]),
        limit=25,
    )
    assert slice_.purchase_list == []
    assert catalog_service.EMPTY_SLICE_EVIDENCE.split()[0] in slice_.evidence


def test_purchase_list_csv_headers_include_value_and_priority():
    csv_text = catalog_service.purchase_list_csv(limit=2)
    header = csv_text.splitlines()[0]
    assert "operational_priority" in header
    assert "estimated_purchase_value" in header

    from app.models import AnalyticalScope

    root_snap, root_items = catalog_service.chat_dashboard(limit=5)
    if not root_snap.by_category:
        pytest.skip("no categories")
    cat = root_snap.by_category[0].category
    scoped_csv = catalog_service.purchase_list_csv(
        limit=5,
        scope=AnalyticalScope(categories=[cat]),
    )
    _, scoped_items = catalog_service.chat_dashboard(
        limit=5,
        scope=AnalyticalScope(categories=[cat]),
    )
    assert scoped_csv.count("\n") == len(scoped_items) + 1  # header + rows


def test_get_replenishment_by_query():
    rec = catalog_service.get_replenishment_by_query(SKU_HIGH_QTY)
    assert rec.product_id == SKU_HIGH_QTY


def test_safe_resolve_unknown():
    assert catalog_service.safe_resolve(SKU_UNKNOWN) is None


def test_format_slice_evidence_with_active_filters():
    from app.models import AnalyticalScope

    scope = AnalyticalScope(
        categories=["Cabello"],
        coverage_buckets=["0–3 días"],
        health_buckets=["stockout_risk"],
        suppliers=["Proveedor X"],
    )
    snap, items = catalog_service.chat_dashboard(limit=5, scope=scope)
    if not items:
        pytest.skip("no items for scope")
    text = catalog_service.format_slice_evidence(snap, items, scope)
    assert "Cabello" in text
    assert "Cobertura activa" in text
    assert "Estado activo" in text
    assert "Proveedores activos" in text


def test_format_purchase_list_answer_empty():
    text = catalog_service.format_purchase_list_answer([])
    assert "no hay productos" in text.lower()


def test_purchase_list_items_shape():
    recs = catalog_service.list_purchase_recommendations(limit=2)
    items = catalog_service.purchase_list_items(recs)
    assert len(items) == len(recs)
    assert items[0].product_id
    assert items[0].operational_priority in {"critical", "high", "normal"}
