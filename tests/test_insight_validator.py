from app.models import CommitSummary, DashboardInsight, PurchasePriority
from app.services import catalog_service, insight_validator


def _slice(limit: int = 5):
    return catalog_service.replenishment_slice(limit=limit)


def test_validate_insight_rejects_unknown_sku():
    slice_data = _slice()
    if not slice_data.purchase_list:
        return
    item = slice_data.purchase_list[0]
    insight = DashboardInsight(
        panel_title="T",
        summary=f"{len(slice_data.purchase_list)} productos",
        purchase_priorities=[
            PurchasePriority(
                product_id="UNKNOWN-SKU",
                product_name="X",
                recommended_quantity=item.recommended_quantity,
                reason="test",
            )
        ],
    )
    errors = insight_validator.validate_insight(insight, slice_data)
    assert any("not in purchase_list" in e for e in errors)


def test_validate_insight_accepts_valid_priority():
    slice_data = _slice()
    if not slice_data.purchase_list:
        return
    item = slice_data.purchase_list[0]
    insight = DashboardInsight(
        panel_title="T",
        summary=str(len(slice_data.purchase_list)),
        purchase_priorities=[
            PurchasePriority(
                product_id=item.product_id,
                product_name=item.product_name,
                recommended_quantity=item.recommended_quantity,
                reason="urgente",
            )
        ],
    )
    errors = insight_validator.validate_insight(insight, slice_data)
    assert errors == []


def test_validate_commit_summary_requires_oc_citation():
    slice_data = _slice()
    n = len(slice_data.purchase_list)
    total = sum(i.recommended_quantity for i in slice_data.purchase_list)
    if n == 0:
        return
    item = slice_data.purchase_list[0]
    bad = CommitSummary(
        headline="H",
        oc_summary="sin numeros",
        top_priorities=[
            PurchasePriority(
                product_id=item.product_id,
                product_name=item.product_name,
                recommended_quantity=item.recommended_quantity,
                reason="r",
            )
        ],
    )
    errors = insight_validator.validate_commit_summary(bad, slice_data)
    assert errors

    good = CommitSummary(
        headline="H",
        oc_summary=f"Exportás {n} SKUs y {total} unidades.",
        top_priorities=bad.top_priorities,
    )
    assert insight_validator.validate_commit_summary(good, slice_data) == []
