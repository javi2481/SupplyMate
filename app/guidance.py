"""Catalog-validated conversational guidance.

The LLM may phrase the question; Python owns which options exist.
"""

from __future__ import annotations

from app.guidance_chips import (
    chip_for_draft_oc,
    chip_for_name_token,
    chip_for_stockout,
    chip_for_subcategory,
    chip_for_todos,
)
from app.guidance_tokens import GUIDE_SKU_THRESHOLD, size_tokens_from_skus
from app.models import (
    AnalyticalScope,
    GuidanceChip,
    GuidanceDecision,
    InventoryDashboard,
    PurchaseListItem,
    ReplenishmentSlice,
    ResolvedReference,
)
from app.missions import MissionEdge
from app.reference_resolver import normalize_text
from app.slice_facets import SliceFacets, list_slice_facets

FACET_SUBCATEGORY = "subcategory"
FACET_SIZE = "size"
FACET_STOCKOUT = "stockout"
FACET_COMPLEMENT = "complement"


def _sku_ids(resolved: list[ResolvedReference]) -> list[str]:
    ids: list[str] = []
    for item in resolved:
        ids.extend(item.sku_ids)
    return list(dict.fromkeys(ids))


def _progress(scope: AnalyticalScope) -> tuple[str, int, int]:
    parts: list[str] = []
    parts.extend(scope.categories[:2])
    parts.extend(scope.subcategories[:2])
    for token in scope.name_tokens[:1]:
        parts.append(token.upper() if token.islower() else token)
    if scope.health_buckets:
        parts.append("quiebre")
    label = " · ".join(parts) if parts else "Recorte"
    done = 0
    total = 4
    if scope.categories or scope.subcategories:
        done += 1
    if scope.subcategories or FACET_SUBCATEGORY in scope.guidance_dismissed:
        done += 1
    if scope.name_tokens or FACET_SIZE in scope.guidance_dismissed:
        done += 1
    if scope.health_buckets or FACET_STOCKOUT in scope.guidance_dismissed:
        done += 1
    return label, min(done, total), total


def _human_subcategory_label(name: str) -> str:
    mapping = {
        "Pañales P/Bebes": "Bebé",
        "Pañales P/Adultos": "Adulto",
        "Desodorantes en Aerosol": "Aerosol",
        "Desodorantes Roll On": "Roll-on",
        "Desodorantes en Barra": "Barra",
        "Desodorantes en Crema": "Crema",
        "Antitranspirantes en Aerosol": "Antitranspirante aerosol",
    }
    return mapping.get(name, name)


def _subcategory_candidates(
    facets: SliceFacets,
    scope: AnalyticalScope,
) -> list[tuple[str, int]]:
    if scope.subcategories or FACET_SUBCATEGORY in scope.guidance_dismissed:
        return []
    if len(facets.subcategories) < 2:
        return []

    baby_adult = [
        (n, c)
        for n, c in facets.subcategories
        if "bebe" in normalize_text(n) or "adult" in normalize_text(n)
    ]
    if len(baby_adult) >= 2:
        return baby_adult[:2]
    return facets.subcategories[:5]


def pick_next_question(
    scope: AnalyticalScope,
    facets: SliceFacets,
    *,
    purchase_items: list[PurchaseListItem],
    dashboard: InventoryDashboard,
) -> GuidanceDecision:
    progress_label, progress_step, progress_total = _progress(scope)

    subcats = _subcategory_candidates(facets, scope)
    if subcats:
        chips = [
            chip_for_subcategory(_human_subcategory_label(name), name)
            for name, _count in subcats
        ]
        question = (
            f"Hay **{facets.sku_count} SKUs** en este recorte. "
            "Para no mezclar grupos, ¿cuál querés analizar primero?"
        )
        names_norm = [normalize_text(n) for n, _ in subcats]
        if (
            len(subcats) == 2
            and any("bebe" in n for n in names_norm)
            and any("adult" in n for n in names_norm)
        ):
            question = f"Hay **{facets.sku_count} SKUs**. ¿Bebé o adulto?"
        return GuidanceDecision(
            action="ask_clarification",
            reason="multiple_subcategories",
            question=question,
            options=[c.label for c in chips],
            chips=chips,
            progress_label=progress_label,
            progress_step=progress_step,
            progress_total=progress_total,
        )

    if (
        len(facets.size_tokens) >= 2
        and not scope.name_tokens
        and FACET_SIZE not in scope.guidance_dismissed
        and facets.sku_count >= GUIDE_SKU_THRESHOLD
    ):
        chips = [chip_for_todos(FACET_SIZE)]
        chips.extend(
            chip_for_name_token(token.upper(), token)
            for token in facets.size_tokens[:5]
        )
        return GuidanceDecision(
            action="ask_clarification",
            reason="multiple_sizes",
            question=(
                f"Hay **{facets.sku_count} SKUs** en este recorte. "
                "Para afinar la reposición, ¿querés analizar todos o un talle?"
            ),
            options=[c.label for c in chips],
            chips=chips,
            progress_label=progress_label,
            progress_step=progress_step,
            progress_total=progress_total,
        )

    if facets.stockout_subset and FACET_STOCKOUT not in scope.guidance_dismissed:
        chips = [chip_for_stockout(), chip_for_todos(FACET_STOCKOUT)]
        return GuidanceDecision(
            action="ask_clarification",
            reason="stockout_subset",
            question=(
                f"**{facets.stockout_count}** de **{facets.sku_count}** SKUs "
                "están en riesgo de quiebre. ¿Solo esos o todo el rubro?"
            ),
            options=[c.label for c in chips],
            chips=chips,
            progress_label=progress_label,
            progress_step=progress_step,
            progress_total=progress_total,
        )

    if facets.mission_neighbors and FACET_COMPLEMENT not in scope.guidance_dismissed:
        edge = facets.mission_neighbors[0]
        preview = preview_union(scope, edge)
        chip = _chip_for_mission(edge)
        if preview.get("qty"):
            chip = chip.model_copy(
                update={
                    "preview_skus": int(preview.get("skus", 0)),
                    "preview_qty": int(preview.get("qty", 0)),
                    "preview_value": preview.get("value"),
                }
            )
        chips = [
            chip,
            GuidanceChip(
                label="No, seguir así",
                action="dismiss_facet",
                args={"facet": FACET_COMPLEMENT},
            ),
        ]
        return GuidanceDecision(
            action="ask_clarification",
            reason="mission_complement",
            question=_complement_question(edge, preview),
            options=[edge.label, "No, seguir así"],
            chips=chips,
            progress_label=progress_label,
            progress_step=progress_step,
            progress_total=progress_total,
        )

    return _draft_oc_decision(
        facets,
        purchase_items,
        dashboard,
        progress_label,
        progress_step,
        progress_total,
    )


def _chip_for_mission(edge: MissionEdge) -> GuidanceChip:
    if edge.to_dimension == "name_token":
        chip = chip_for_name_token(edge.label, edge.to_group, union=True)
    else:
        chip = chip_for_subcategory(edge.label, edge.to_group, union=True)
    if edge.reason_label:
        chip = chip.model_copy(update={"caption": edge.reason_label})
    return chip


def preview_union(scope: AnalyticalScope, edge: MissionEdge) -> dict[str, float | int]:
    from app.services import catalog_service
    from app.services import scope as scope_svc

    before, _ = catalog_service.chat_dashboard(scope=scope)
    trial = scope.model_copy(deep=True)
    if edge.to_dimension == "subcategory":
        trial = scope_svc.add(trial, "subcategory", edge.to_group)
    elif edge.to_dimension == "name_token":
        trial = scope_svc.add(trial, "name_token", edge.to_group)
    after, items = catalog_service.chat_dashboard(limit=100, scope=trial)
    qty = sum(i.recommended_quantity for i in items)
    value = after.estimated_purchase_value or 0.0
    return {
        "skus": after.skus,
        "qty": qty,
        "value": float(value) if value else 0.0,
        "added_skus": max(0, after.skus - before.skus),
    }


def _complement_question(edge: MissionEdge, preview: dict | None) -> str:
    reason_suffix = f" {edge.reason_label}." if edge.reason_label else ""
    if preview and preview.get("qty"):
        return (
            f"¿Sumamos también **{edge.label}**?{reason_suffix} "
            f"Serían ~**{int(preview['qty'])}** u. en ese grupo."
        )
    if edge.reason_label:
        return f"¿Querés sumar **{edge.label}** a este recorte? {edge.reason_label}"
    return f"¿Querés sumar **{edge.label}** a este recorte?"


def _draft_oc_decision(
    facets: SliceFacets,
    purchase_items: list[PurchaseListItem],
    dashboard: InventoryDashboard,
    progress_label: str,
    progress_step: int,
    progress_total: int,
) -> GuidanceDecision:
    total_qty = sum(i.recommended_quantity for i in purchase_items)
    value = dashboard.estimated_purchase_value
    value_txt = f" · **${value:,.0f}** estimado" if value else ""
    chip = chip_for_draft_oc()
    return GuidanceDecision(
        action="draft_oc",
        reason="ready_for_oc",
        question=(
            f"Con este recorte hay **{len(purchase_items)}** líneas a reponer "
            f"({total_qty} u.{value_txt}). ¿Armamos la OC?"
        ),
        options=[chip.label],
        chips=[chip],
        progress_label=progress_label,
        progress_step=progress_total,
        progress_total=progress_total,
    )


def guidance_after_slice(slice_data: ReplenishmentSlice) -> GuidanceDecision:
    facets = list_slice_facets(
        slice_data.scope,
        slice_data.dashboard,
        slice_data.purchase_list,
    )
    return pick_next_question(
        slice_data.scope,
        facets,
        purchase_items=slice_data.purchase_list,
        dashboard=slice_data.dashboard,
    )


def guidance_for_resolution(
    resolved: list[ResolvedReference],
    scope: AnalyticalScope,
) -> GuidanceDecision:
    from app.services import catalog_service

    slice_data = catalog_service.replenishment_slice(scope, limit=25)
    return guidance_after_slice(slice_data)


def is_valid_guidance_option(option: str, sku_ids: list[str]) -> bool:
    token = normalize_text(option)
    if token == "todos":
        return True
    return token in size_tokens_from_skus(sku_ids)
