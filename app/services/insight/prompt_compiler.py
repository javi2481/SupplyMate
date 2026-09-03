"""Deterministic prompt builder for /replenishment/analyze."""

from __future__ import annotations

import hashlib
import json

from app.core.models import (
    AnalyticalScope,
    InteractionEvent,
    InventoryDashboard,
    PanelMode,
    PurchaseListItem,
    ReplenishmentSlice,
)
from app.guidance.missions import mission_neighbors
from app.services.analytics import metrics


def _event_line(index: int, event: InteractionEvent) -> str:
    label = event.label_human or event.value or event.action
    return f"{index}. [{event.source}] {event.action}: {label}"


def _dashboard_summary(dash: InventoryDashboard) -> dict:
    return {
        "skus": dash.skus,
        "stockout_risk": dash.stockout_risk,
        "understock": dash.understock,
        "overstock": dash.overstock,
        "healthy": dash.healthy,
        "avg_coverage": dash.avg_coverage,
        "estimated_purchase_value": dash.estimated_purchase_value,
    }


def _purchase_top(items: list[PurchaseListItem], limit: int = 10) -> list[dict]:
    return [
        {
            "product_id": item.product_id,
            "product_name": item.product_name,
            "recommended_quantity": item.recommended_quantity,
            "days_of_supply": item.days_of_supply,
            "health_bucket": item.health_bucket,
            "operational_priority": item.operational_priority,
            "estimated_purchase_value": item.estimated_purchase_value,
            "category": item.category,
        }
        for item in items[:limit]
    ]


def _delta_vs_root(slice_dash: InventoryDashboard, root_dash: InventoryDashboard) -> dict:
    root_cov = root_dash.avg_coverage
    slice_cov = slice_dash.avg_coverage
    return {
        "skus_delta": slice_dash.skus - root_dash.skus,
        "stockout_risk_delta": slice_dash.stockout_risk - root_dash.stockout_risk,
        "avg_coverage_root": root_cov,
        "avg_coverage_slice": slice_cov,
    }


def _related_complements(scope: AnalyticalScope) -> list[dict[str, str]]:
    return [
        {"label": edge.label, "reason": edge.reason}
        for edge in mission_neighbors(scope)
    ]


def compile_analyze_prompt(
    *,
    mode: PanelMode,
    root_question: str,
    events: list[InteractionEvent],
    slice_data: ReplenishmentSlice,
    root_dashboard: InventoryDashboard,
) -> str:
    history = "\n".join(_event_line(i + 1, e) for i, e in enumerate(events))
    payload = {
        "dashboard": _dashboard_summary(slice_data.dashboard),
        "delta_vs_root": _delta_vs_root(slice_data.dashboard, root_dashboard),
        "purchase_list_top": _purchase_top(slice_data.purchase_list),
        "evidence": slice_data.evidence,
        "scope": slice_data.scope.model_dump(),
    }
    related = _related_complements(slice_data.scope)
    if related:
        payload["related"] = related
    payload_json = json.dumps(payload, ensure_ascii=False, indent=2)

    if mode == "commit":
        task = (
            "Modo ARMAR OC (confirmación). Resumí la orden de compra del recorte congelado. "
            "NO sugieras nuevos filtros. Citá solo números del JSON. "
            "Respondé SOLO con JSON válido matching CommitSummary: "
            "headline, oc_summary, top_priorities (max 3), checklist (max 4)."
        )
    else:
        task = (
            "Modo EXPLORAR (Ask). Explicá por qué este recorte importa vs inventario total. "
            "Priorizá qué comprar primero usando solo SKUs del purchase_list_top. "
            "Si el payload incluye related, podés mencionar esos complementos usando label y reason. "
            "NO afirmes co-ocurrencia transaccional (ej. 'quienes compran X suelen comprar Y'). "
            "Sugerí preguntas siguientes y hints de navegación. "
            "Respondé SOLO con JSON válido matching DashboardInsight: "
            "panel_title, summary, bullets, purchase_priorities, navigation_hints, "
            "suggested_questions, highlight_kpis."
        )

    parts = [
        "Sos SupplyMate Analista. Español. Usá SOLO números del JSON payload.",
        metrics.metric_prompt_block(),
        "No uses porcentajes ni variaciones salvo que aparezcan en el JSON.",
        f"Pregunta inicial: {root_question or '(no indicada)'}",
        f"Historial de exploración:\n{history or '(ninguno)'}",
        f"Payload verificado:\n{payload_json}",
        task,
    ]
    return "\n\n".join(parts)


def prompt_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
