"""Tests for live KPI and table column policies."""

from __future__ import annotations

from app.services.analytics import metrics
from ui.composition.kpi_policy import commit_kpi_cards, explore_kpi_cards
from ui.composition.table_policy import EXPLORE_COLUMNS, SIGNAL_COLUMN, build_explore_rows
from ui.theme import HEALTH_COLORS, SHELL_TOKENS


def test_explore_kpis_exclude_oc_lines_and_value():
    cards = explore_kpi_cards(
        {
            "skus": 441,
            "understock": 74,
            "stockout_risk": 18,
            "overstock": 9,
            "avg_coverage": 6.4,
            "estimated_purchase_value": 9999,
        },
        purchase_lines=38,
    )
    labels = [c.label for c in cards]
    assert labels == ["Productos", "Falta de stock", "Riesgo de quiebre", "Cobertura prom."]
    assert "Líneas de OC" not in labels
    assert "Valor estimado" not in labels
    assert cards[0].value == "441"
    assert cards[3].value == "6.4 d"
    assert cards[0].icon_key == "products"
    assert cards[1].icon_key == "understock"
    assert cards[2].icon_key == "stockout_risk"
    assert cards[3].icon_key == "coverage"


def test_explore_kpi_accents_use_brand_blue_and_health():
    brand = SHELL_TOKENS["primary_accent"]
    cards = explore_kpi_cards(
        {
            "skus": 10,
            "understock": 2,
            "stockout_risk": 1,
            "avg_coverage": 5.0,
        }
    )
    by_label = {c.label: c.accent for c in cards}
    assert by_label["Productos"] == brand
    assert by_label["Cobertura prom."] == brand
    assert by_label["Falta de stock"] == HEALTH_COLORS[metrics.BUCKET_UNDERSTOCK]
    assert by_label["Riesgo de quiebre"] == HEALTH_COLORS[metrics.BUCKET_STOCKOUT_RISK]
    assert HEALTH_COLORS[metrics.BUCKET_UNDERSTOCK] == "#FB8C00"
    assert HEALTH_COLORS[metrics.BUCKET_STOCKOUT_RISK] == "#E53935"


def test_commit_kpis_include_oc_and_priorities():
    cards = commit_kpi_cards(
        [
            {
                "recommended_quantity": 10,
                "operational_priority": "critical",
                "estimated_purchase_value": 100,
            },
            {
                "recommended_quantity": 5,
                "operational_priority": "high",
                "estimated_purchase_value": 50,
            },
            {
                "recommended_quantity": 1,
                "operational_priority": "normal",
                "estimated_purchase_value": 10,
            },
        ]
    )
    by_label = {c.label: c.value for c in cards}
    assert by_label["Líneas de OC"] == "3"
    assert by_label["Unidades"] == "16"
    assert by_label["Críticas"] == "1"
    assert by_label["Altas"] == "1"
    assert "Valor estimado" in by_label
    assert all(card.icon_key is None for card in cards)


def test_explore_table_column_order_and_signal_rename():
    assert EXPLORE_COLUMNS[:6] == [
        "Prioridad",
        "Producto",
        "Pedir",
        "Cobertura (días)",
        "Stock",
        "Proveedor",
    ]
    assert SIGNAL_COLUMN == "Señal"
    assert "Tendencia" not in EXPLORE_COLUMNS
    rows = build_explore_rows(
        [
            {
                "product_id": "1",
                "product_name": "Pañal XXG",
                "supplier": "Prov",
                "current_stock": 4,
                "days_of_supply": 2.0,
                "recommended_quantity": 12,
                "operational_priority": "critical",
                "health_bucket": "stockout_risk",
                "average_daily_demand": 3.2,
                "estimated_purchase_value": 80,
            }
        ]
    )
    assert list(rows[0].keys()) == EXPLORE_COLUMNS
    assert rows[0]["Producto"] == "Pañal XXG"
    assert rows[0]["Pedir"] == 12
    assert "SKU" not in rows[0]
    assert rows[0]["Señal"] == "↓ quiebre"
