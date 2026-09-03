"""Which KPIs belong on live Explore vs Commit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.analytics import metrics
from ui.theme import HEALTH_COLORS


@dataclass(frozen=True)
class KpiCard:
    label: str
    value: str
    accent: str
    hint: str


def _fmt_coverage(avg: Any) -> str:
    if isinstance(avg, (int, float)):
        return f"{avg:.1f} d"
    return "—"


def explore_kpi_cards(
    dash: dict | None,
    *,
    purchase_lines: int | None = None,
) -> list[KpiCard]:
    del purchase_lines
    dash = dash or {}
    return [
        KpiCard(
            metrics.LABEL_SKUS,
            str(dash.get("skus", "—")),
            "#90CAF9",
            "SKUs en el recorte actual",
        ),
        KpiCard(
            metrics.LABEL_UNDERSTOCK,
            str(dash.get("understock", "—")),
            HEALTH_COLORS[metrics.BUCKET_UNDERSTOCK],
            "Necesitan reposición calculada",
        ),
        KpiCard(
            metrics.LABEL_STOCKOUT_RISK,
            str(dash.get("stockout_risk", "—")),
            HEALTH_COLORS[metrics.BUCKET_STOCKOUT_RISK],
            metrics.METRIC_CONTRACTS["stockout_risk"].caveat,
        ),
        KpiCard(
            f"{metrics.LABEL_COVERAGE} prom.",
            _fmt_coverage(dash.get("avg_coverage")),
            "#AED581",
            metrics.METRIC_CONTRACTS["coverage"].caveat,
        ),
    ]


def commit_kpi_cards(purchase_list: list[dict] | None) -> list[KpiCard]:
    items = purchase_list or []
    units = sum(int(item.get("recommended_quantity") or 0) for item in items)
    critical = sum(1 for item in items if item.get("operational_priority") == "critical")
    high = sum(1 for item in items if item.get("operational_priority") == "high")
    value = sum(
        float(item.get("estimated_purchase_value") or 0) for item in items
    )
    cards = [
        KpiCard("Líneas de OC", str(len(items)), "#81D4FA", "Productos en la OC propuesta"),
        KpiCard("Unidades", str(units), "#90CAF9", "Cantidad recomendada total"),
        KpiCard("Críticas", str(critical), HEALTH_COLORS[metrics.BUCKET_STOCKOUT_RISK], "Prioridad crítica"),
        KpiCard("Altas", str(high), HEALTH_COLORS[metrics.BUCKET_UNDERSTOCK], "Prioridad alta"),
    ]
    if value:
        cards.append(
            KpiCard(
                metrics.LABEL_PURCHASE_VALUE,
                f"{value:,.0f}",
                "#FFCC80",
                metrics.METRIC_CONTRACTS["purchase_value"].caveat,
            )
        )
    return cards
