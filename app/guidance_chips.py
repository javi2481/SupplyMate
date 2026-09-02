"""Apply validated guidance chips without re-interpreting through the LLM."""

from __future__ import annotations

from app.models import AnalyticalScope, GuidanceChip
from app.services import metrics
from app.services import scope as scope_svc


def apply_guidance_chip(
    scope: AnalyticalScope,
    chip: GuidanceChip,
) -> tuple[AnalyticalScope, bool]:
    """Return updated scope and whether to enter commit (draft OC) mode."""
    action = chip.action
    args = chip.args

    if action == "add_subcategory":
        return scope_svc.add(scope, "subcategory", args["subcategory"]), False
    if action == "add_category":
        return scope_svc.add(scope, "category", args["category"]), False
    if action == "add_name_token":
        return scope_svc.add(scope, "name_token", args["name_token"]), False
    if action == "add_health_bucket":
        return scope_svc.add(scope, "health_bucket", args["health_bucket"]), False
    if action == "dismiss_facet":
        return scope_svc.dismiss_guidance(scope, args.get("facet", "")), False
    if action == "union_subcategory":
        return scope_svc.add(scope, "subcategory", args["subcategory"]), False
    if action == "union_name_token":
        return scope_svc.add(scope, "name_token", args["name_token"]), False
    if action == "draft_oc":
        return scope, True
    if action == "keep_all":
        facet = args.get("facet", "size")
        return scope_svc.dismiss_guidance(scope, facet), False

    return scope, False


def chip_for_subcategory(label: str, value: str, *, union: bool = False) -> GuidanceChip:
    action = "union_subcategory" if union else "add_subcategory"
    return GuidanceChip(label=label, action=action, args={"subcategory": value})


def chip_for_name_token(label: str, token: str, *, union: bool = False) -> GuidanceChip:
    action = "union_name_token" if union else "add_name_token"
    return GuidanceChip(label=label, action=action, args={"name_token": token})


def chip_for_stockout() -> GuidanceChip:
    return GuidanceChip(
        label="Solo riesgo de quiebre",
        action="add_health_bucket",
        args={"health_bucket": metrics.BUCKET_STOCKOUT_RISK},
    )


def chip_for_todos(facet: str = "size") -> GuidanceChip:
    return GuidanceChip(
        label="Todos",
        action="keep_all",
        args={"facet": facet},
    )


def chip_for_draft_oc() -> GuidanceChip:
    return GuidanceChip(
        label="Armar OC de este recorte",
        action="draft_oc",
        args={},
    )
