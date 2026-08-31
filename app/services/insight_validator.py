"""Validate LLM insight output against deterministic slice payload."""

from __future__ import annotations

import json
import re
from typing import Any

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


def _add_number(nums: set[str], value: Any) -> None:
    if value is None:
        return
    if isinstance(value, bool):
        return
    if isinstance(value, int):
        nums.add(str(value))
        return
    if isinstance(value, float):
        nums.add(str(int(value)))
        rounded = int(round(value))
        nums.add(str(rounded))
        nums.add(f"{value:.1f}")
        nums.add(f"{value:.2f}")
        return
    text = str(value).strip()
    if re.fullmatch(r"\d+", text):
        nums.add(text)


def allowed_numbers_from_mapping(data: Any) -> set[str]:
    """Harvest integer tokens from a JSON-serializable payload."""
    nums: set[str] = set()
    blob = json.dumps(data, default=str, ensure_ascii=False)
    for match in re.finditer(r"\b(\d+)\b", blob):
        nums.add(match.group(1))
    return nums


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
        _add_number(nums, val)
    _add_number(nums, dash.avg_coverage)
    _add_number(nums, dash.estimated_purchase_value)
    total_qty = sum(i.recommended_quantity for i in slice_data.purchase_list)
    _add_number(nums, len(slice_data.purchase_list))
    _add_number(nums, total_qty)
    for item in slice_data.purchase_list:
        _add_number(nums, item.recommended_quantity)
        _add_number(nums, item.days_of_supply)
        _add_number(nums, item.estimated_purchase_value)
        _add_number(nums, item.purchase_cost)
        _add_number(nums, item.current_stock)
    return nums


def orphan_integers(text: str, allowed: set[str]) -> list[str]:
    errors: list[str] = []
    for match in re.finditer(r"\b(\d+)\b", text):
        token = match.group(1)
        if token not in allowed and int(token) > 2:
            errors.append(f"orphan integer {token} in text")
    return errors


def _orphan_integers(text: str, allowed: set[str]) -> list[str]:
    return orphan_integers(text, allowed)


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
    errors.extend(orphan_integers(blob, allowed))
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
    errors.extend(orphan_integers(blob, allowed))
    return errors


def validate_explanation_text(text: str, payload: dict) -> list[str]:
    allowed = allowed_numbers_from_mapping(payload)
    return orphan_integers(text, allowed)
