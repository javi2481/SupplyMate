import json

from app.core.models import CommitSummary, DashboardInsight, PurchasePriority
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


def test_validate_insight_rejects_orphan_integer():
    slice_data = _slice()
    if not slice_data.purchase_list:
        return
    insight = DashboardInsight(
        panel_title="T",
        summary="El recorte mejora un 999 por magia",
        bullets=[],
    )
    errors = insight_validator.validate_insight(insight, slice_data)
    assert any("orphan integer 999" in e for e in errors)


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


def test_insight_eval_fixtures_cover_schema_and_facts():
    slice_data = _slice()
    if not slice_data.purchase_list:
        return
    item = slice_data.purchase_list[0]
    n = len(slice_data.purchase_list)
    total = sum(i.recommended_quantity for i in slice_data.purchase_list)
    cases = [
        {
            "name": "valid_priority",
            "expect_errors": False,
            "insight": {
                "panel_title": "T",
                "summary": str(n),
                "bullets": [str(total)],
                "purchase_priorities": [
                    {
                        "product_id": item.product_id,
                        "product_name": item.product_name,
                        "recommended_quantity": item.recommended_quantity,
                        "reason": "ok",
                    }
                ],
            },
        },
        {
            "name": "wrong_qty",
            "expect_errors": True,
            "insight": {
                "panel_title": "T",
                "summary": str(n),
                "purchase_priorities": [
                    {
                        "product_id": item.product_id,
                        "product_name": item.product_name,
                        "recommended_quantity": item.recommended_quantity + 11,
                        "reason": "bad",
                    }
                ],
            },
        },
        {
            "name": "unknown_sku",
            "expect_errors": True,
            "insight": {
                "panel_title": "T",
                "summary": str(n),
                "purchase_priorities": [
                    {
                        "product_id": "NO-SUCH",
                        "product_name": "X",
                        "recommended_quantity": item.recommended_quantity,
                        "reason": "bad",
                    }
                ],
            },
        },
        {
            "name": "orphan_claim",
            "expect_errors": True,
            "insight": {
                "panel_title": "T",
                "summary": "caemos 888 puntos",
                "purchase_priorities": [],
            },
        },
    ]
    for case in cases:
        insight = DashboardInsight.model_validate(case["insight"])
        errors = insight_validator.validate_insight(insight, slice_data)
        if case["expect_errors"]:
            assert errors, case["name"]
        else:
            assert errors == [], (case["name"], errors)
    assert json.dumps(cases)


def test_validate_explanation_rejects_orphan():
    payload = {"recommended_quantity": 12, "current_stock": 4}
    errors = insight_validator.validate_explanation_text(
        "Pedí 999 unidades", payload
    )
    assert any("999" in e for e in errors)


def test_validate_explanation_accepts_payload_numbers():
    payload = {"recommended_quantity": 12, "current_stock": 4}
    assert (
        insight_validator.validate_explanation_text(
            "Pedí 12 unidades con stock 4", payload
        )
        == []
    )
