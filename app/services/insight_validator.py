"""Validate LLM insight output against deterministic slice payload."""

from __future__ import annotations

import re

from app.models import CommitSummary, DashboardInsight, PurchaseListItem, ReplenishmentSlice


def _items_by_id(items: list[PurchaseListItem]) -> dict[str, PurchaseListItem]:
    return {item.product_id: item for item in items if item.product_id}


def _validate_priorities(
    priorities: list,
    items_by_id: dict[str, PurchaseListItem],
    *,
    label: str,
) -> list[str]:
    errors: list[str] = []
    for idx, pri in enumerate(priorities):
        pid = pri.product_id
        if pid not in items_by_id:
            errors.append(f"{label}[{idx}] product_id {pid!r} not in purchase_list")
            continue
        expected_qty = items_by_id[pid].recommended_quantity
        if pri.recommended_quantity != expected_qty:
            errors.append(
                f"{label}[{idx}] qty {pri.recommended_quantity} != {expected_qty}"
            )
    return errors


def _allowed_numbers(slice_data: ReplenishmentSlice) -> set[str]:
    nums: set[str] = set()
    dash = slice_data.dashboard
    for val in (
        dash.skus,
        dash.stockout_risk,
        dash.understock,
        dash.overstock,
        dash.healthy,
    ):
        nums.add(str(val))
    if dash.avg_coverage is not None:
        nums.add(f"{dash.avg_coverage:.1f}")
        nums.add(str(int(dash.avg_coverage)))
    total_qty = sum(i.recommended_quantity for i in slice_data.purchase_list)
    nums.add(str(len(slice_data.purchase_list)))
    nums.add(str(total_qty))
    for item in slice_data.purchase_list:
        nums.add(str(item.recommended_quantity))
        if item.days_of_supply is not None:
            nums.add(f"{item.days_of_supply:.1f}")
    return nums


def _orphan_integers(text: str, allowed: set[str]) -> list[str]:
    errors: list[str] = []
    for match in re.finditer(r"\b(\d+)\b", text):
        token = match.group(1)
        if token not in allowed and int(token) > 2:
            errors.append(f"orphan integer {token} in text")
    return errors


def validate_insight(
    insight: DashboardInsight,
    slice_data: ReplenishmentSlice,
) -> list[str]:
    items_by_id = _items_by_id(slice_data.purchase_list)
    errors = _validate_priorities(
        insight.purchase_priorities, items_by_id, label="purchase_priorities"
    )
    allowed = _allowed_numbers(slice_data)
    blob = " ".join(insight.bullets + [insight.summary])
    errors.extend(_orphan_integers(blob, allowed))
    return errors


def validate_commit_summary(
    summary: CommitSummary,
    slice_data: ReplenishmentSlice,
) -> list[str]:
    items_by_id = _items_by_id(slice_data.purchase_list)
    errors = _validate_priorities(
        summary.top_priorities, items_by_id, label="top_priorities"
    )
    allowed = _allowed_numbers(slice_data)
    n = len(slice_data.purchase_list)
    total = sum(i.recommended_quantity for i in slice_data.purchase_list)
    if str(n) not in summary.oc_summary and str(total) not in summary.oc_summary:
        if n > 0:
            errors.append("oc_summary must cite sku count or total units from payload")
    blob = " ".join([summary.headline, summary.oc_summary] + summary.checklist)
    errors.extend(_orphan_integers(blob, allowed))
    return errors
