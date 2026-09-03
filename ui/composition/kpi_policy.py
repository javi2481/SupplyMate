"""Which KPIs belong on live Explore vs Commit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.analytics import metrics
from ui.theme import HEALTH_COLORS, SHELL_TOKENS


@dataclass(frozen=True)
class KpiCard:
    label: str
    value: str
    accent: str
    hint: str
    icon_key: str | None = None


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
    brand = SHELL_TOKENS["primary_accent"]
    return [
        KpiCard(
            metrics.LABEL_SKUS,
            str(dash.get("skus", "—")),
            brand,
            "SKUs en el recorte actual",
            icon_key="products",
        ),
        KpiCard(
            metrics.LABEL_UNDERSTOCK,
            str(dash.get("understock", "—")),
            HEALTH_COLORS[metrics.BUCKET_UNDERSTOCK],
            "Necesitan reposición calculada",
            icon_key="understock",
        ),
        KpiCard(
            metrics.LABEL_STOCKOUT_RISK,
            str(dash.get("stockout_risk", "—")),
            HEALTH_COLORS[metrics.BUCKET_STOCKOUT_RISK],
            metrics.METRIC_CONTRACTS["stockout_risk"].caveat,
            icon_key="stockout_risk",
        ),
        KpiCard(
            f"{metrics.LABEL_COVERAGE} prom.",
            _fmt_coverage(dash.get("avg_coverage")),
            brand,
            metrics.METRIC_CONTRACTS["coverage"].caveat,
            icon_key="coverage",
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
