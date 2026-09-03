"""Componentes visuales didácticos para Streamlit."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pandas as pd
import streamlit as st

from app.services import metrics
from ui import theme
from ui.composition.kpi_policy import KpiCard
from ui.composition.table_policy import EXPLORE_COLUMNS, build_explore_rows


def inject_theme() -> None:
    st.markdown(theme.CSS, unsafe_allow_html=True)


def _kpi_icon(icon_key: str | None) -> str:
    if not icon_key:
        return ""
    icon = getattr(theme, "KPI_ICONS", {}).get(icon_key)
    if not icon:
        return ""
    return f'<span class="sm-kpi-icon" aria-hidden="true">{icon}</span>'


def _kpi_card(label: str, value: str, accent: str, hint: str, icon_key: str | None = None) -> str:
    icon = _kpi_icon(icon_key)
    return f"""
<div class="sm-kpi" style="--sm-accent: {accent};">
  <div class="sm-kpi-top">
    {icon}
    <div class="sm-kpi-copy">
      <div class="sm-kpi-label">{label}</div>
      <div class="sm-kpi-value">{value}</div>
    </div>
  </div>
  <div class="sm-kpi-hint">{hint}</div>
</div>
"""


def render_kpi_cards(cards: list[KpiCard]) -> None:
    html = "".join(
        _kpi_card(card.label, card.value, card.accent, card.hint, card.icon_key) for card in cards
    )
    st.markdown(f'<div class="sm-kpi-row">{html}</div>', unsafe_allow_html=True)


def render_chart_card(title: str, *, caption: str | None = None, body: Callable[[], None]) -> None:
    st.markdown("<div class='sm-chart-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='sm-chart-card-title'>{title}</div>", unsafe_allow_html=True)
    if caption:
        st.caption(caption)
    body()
    st.markdown("</div>", unsafe_allow_html=True)


def render_kpi_strip(dash: dict | None, *, purchase_lines: int | None = None) -> None:
    dash = dash or {}
    avg = dash.get("avg_coverage")
    avg_txt = f"{avg:.1f} d" if isinstance(avg, (int, float)) else "—"
    skus = dash.get("skus", "—")
    oc_lines = purchase_lines if purchase_lines is not None else "—"
    cards = [
        _kpi_card(
            metrics.LABEL_SKUS,
            str(skus),
            "#90CAF9",
            "SKUs en el recorte actual",
        ),
        _kpi_card(
            "Líneas de OC",
            str(oc_lines),
            "#81D4FA",
            "Productos con cantidad a reponer en este recorte",
        ),
        _kpi_card(
            metrics.LABEL_STOCKOUT_RISK,
            str(dash.get("stockout_risk", "—")),
            theme.HEALTH_COLORS[metrics.BUCKET_STOCKOUT_RISK],
            metrics.METRIC_CONTRACTS["stockout_risk"].caveat,
        ),
        _kpi_card(
            metrics.LABEL_UNDERSTOCK,
            str(dash.get("understock", "—")),
            theme.HEALTH_COLORS[metrics.BUCKET_UNDERSTOCK],
            "Necesitan reposición calculada",
        ),
        _kpi_card(
            metrics.LABEL_OVERSTOCK,
            str(dash.get("overstock", "—")),
            theme.HEALTH_COLORS[metrics.BUCKET_OVERSTOCK],
            metrics.METRIC_CONTRACTS["overstock"].caveat,
        ),
        _kpi_card(
            f"{metrics.LABEL_COVERAGE} prom.",
            avg_txt,
            "#AED581",
            metrics.METRIC_CONTRACTS["coverage"].caveat,
        ),
    ]
    value = dash.get("estimated_purchase_value")
    if isinstance(value, (int, float)):
        cards.append(
            _kpi_card(
                metrics.LABEL_PURCHASE_VALUE,
                f"{value:,.0f}",
                "#FFCC80",
                metrics.METRIC_CONTRACTS["purchase_value"].caveat,
            )
        )
    st.markdown(
        f'<div class="sm-kpi-row">{"".join(cards)}</div>',
        unsafe_allow_html=True,
    )


def render_health_legend() -> None:
    badges = []
    for key, label in metrics.BUCKET_LABELS.items():
        icon = theme.HEALTH_ICONS.get(key, "⚪")
        color = theme.HEALTH_COLORS.get(key, "#888")
        hint = theme.HEALTH_HINTS.get(key, "")
        badges.append(
            f'<span class="sm-badge" style="border-color:{color};">'
            f'{icon} {label}</span>'
        )
    st.markdown(
        f'<div class="sm-legend">{"".join(badges)}</div>',
        unsafe_allow_html=True,
    )
    with st.expander("¿Qué significan estos indicadores?", expanded=False):
        lines = [
            f"- **{c.label}** — {c.rule}. _{c.caveat}_"
            for c in metrics.METRIC_CONTRACTS.values()
        ]
        st.markdown("\n".join(lines))


def render_coverage_strip(coverage_rows: list[dict]) -> None:
    if not coverage_rows:
        return
    total = sum(int(r.get("sku_count") or 0) for r in coverage_rows) or 1
    segments = []
    for row in coverage_rows:
        bucket = str(row.get("bucket") or "")
        count = int(row.get("sku_count") or 0)
        if count <= 0:
            continue
        pct = 100 * count / total
        color = theme.COVERAGE_COLORS.get(bucket, "#546E7A")
        segments.append(
            f'<div title="{bucket}: {count} SKUs" style="flex:{count};'
            f"background:{color};min-width:4px;height:10px;border-radius:2px;"
            f'"></div>'
        )
    if segments:
        st.caption("Mapa de cobertura del recorte (más rojo = menos días)")
        st.markdown(
            f'<div style="display:flex;gap:2px;width:100%;border-radius:4px;overflow:hidden;">'
            f'{"".join(segments)}</div>',
            unsafe_allow_html=True,
        )


def build_purchase_dataframe(purchase_list: list[dict]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for item in purchase_list:
        bucket = str(item.get("health_bucket") or "")
        dos = item.get("days_of_supply")
        coverage_val = float(dos) if dos is not None else 0.0
        rows.append(
            {
                "SKU": item.get("product_id", ""),
                "Producto": item.get("product_name", ""),
                "Proveedor": item.get("supplier", ""),
                "Stock": int(item.get("current_stock") or 0),
                "Cobertura (días)": min(coverage_val, 30.0),
                "Ritmo/día": round(float(item.get("average_daily_demand") or 0), 1),
                "Señal": theme.TREND_LABELS.get(bucket, "—"),
                "Pedir": int(item.get("recommended_quantity") or 0),
                "Prioridad": metrics.PRIORITY_LABELS.get(
                    str(item.get("operational_priority") or ""),
                    item.get("operational_priority") or "—",
                ),
                "Valor est.": item.get("estimated_purchase_value"),
                "Estado": metrics.BUCKET_LABELS.get(bucket, bucket),
            }
        )
    return pd.DataFrame(rows)


def render_purchase_table(
    purchase_list: list[dict],
    *,
    table_key: str = "purchase_table",
    selectable: bool = False,
) -> Any:
    df = build_purchase_dataframe(purchase_list)
    column_config = {
        "Señal": st.column_config.TextColumn(
            "Señal",
            width="small",
            help="Estado de salud del SKU (no es una serie temporal)",
        ),
        "Cobertura (días)": st.column_config.ProgressColumn(
            "Cobertura (días)",
            help="Días de stock al ritmo de venta actual (máx. barra = 30 días)",
            min_value=0,
            max_value=30,
            format="%.1f d",
        ),
        "Ritmo/día": st.column_config.NumberColumn(
            "Ritmo/día",
            help="Unidades vendidas por día (promedio 30 días)",
            format="%.1f u/d",
        ),
        "Pedir": st.column_config.NumberColumn(
            "Pedir",
            help=metrics.LABEL_RECOMMENDED_QTY,
            format="%d u",
        ),
        "Prioridad": st.column_config.TextColumn(
            "Prioridad",
            help="Crítica = riesgo de quiebre; Alta = reponer con cobertura < 7 días",
        ),
        "Valor est.": st.column_config.NumberColumn(
            "Valor est.",
            help=metrics.METRIC_CONTRACTS["purchase_value"].caveat,
            format="%.0f",
        ),
        "Estado": st.column_config.TextColumn("Estado"),
    }
    kwargs: dict[str, Any] = {
        "width": "stretch",
        "hide_index": True,
        "column_config": column_config,
    }
    if selectable:
        kwargs["on_select"] = "rerun"
        kwargs["selection_mode"] = "single-row"
        kwargs["key"] = table_key
    return st.dataframe(df, **kwargs)


def render_explore_table(
    purchase_list: list[dict],
    *,
    table_key: str = "purchase_table",
    selectable: bool = False,
) -> Any:
    df = pd.DataFrame(build_explore_rows(purchase_list), columns=EXPLORE_COLUMNS)
    kwargs: dict[str, Any] = {
        "width": "stretch",
        "hide_index": True,
        "column_config": {
            "Cobertura (días)": st.column_config.ProgressColumn(
                "Cobertura (días)",
                help="Días de stock al ritmo de venta actual (máx. barra = 30 días)",
                min_value=0,
                max_value=30,
                format="%.1f d",
            ),
            "Pedir": st.column_config.NumberColumn("Pedir", format="%d u"),
            "Señal": st.column_config.TextColumn(
                "Señal",
                help="Estado de salud del SKU (no es una serie temporal)",
            ),
        },
        "column_order": EXPLORE_COLUMNS,
    }
    if selectable:
        kwargs["on_select"] = "rerun"
        kwargs["selection_mode"] = "single-row"
        kwargs["key"] = table_key
    return st.dataframe(df, **kwargs)


def render_oc_summary(purchase_list: list[dict]) -> None:
    total = sum(int(item.get("recommended_quantity") or 0) for item in purchase_list)
    stockout = sum(
        1
        for item in purchase_list
        if item.get("health_bucket") == metrics.BUCKET_STOCKOUT_RISK
    )
    st.markdown(
        f'<div class="sm-tip">'
        f"📦 <b>{len(purchase_list)}</b> productos para la OC · "
        f"<b>{total}</b> unidades · "
        f"<b>{stockout}</b> en 🔴 riesgo de quiebre"
        f"</div>",
        unsafe_allow_html=True,
    )
