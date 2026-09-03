"""Altair charts for SupplyMate drill-down (static + selectable)."""

from __future__ import annotations

from typing import Any

import altair as alt
import pandas as pd

from ui.theme import COVERAGE_COLORS


def _qty_color_scale() -> alt.Scale:
    return alt.Scale(scheme="orangered")


def _point_param(selection_name: str, field: str) -> alt.Parameter:
    return alt.selection_point(
        name=selection_name,
        fields=[field],
        nearest=True,
        toggle=False,
    )


def lollipop(
    rows: list[dict],
    y_field: str,
    y_title: str,
    x_field: str = "recommended_quantity",
    x_title: str = "Cantidad recomendada",
    extra_tooltips: list[alt.Tooltip] | None = None,
    *,
    selectable_field: str | None = None,
    selection_name: str = "chart_select",
) -> alt.Chart:
    df = pd.DataFrame(rows)
    tooltips = [
        alt.Tooltip(f"{y_field}:N", title=y_title),
        *(extra_tooltips or []),
        alt.Tooltip(f"{x_field}:Q", title=x_title),
    ]
    x = alt.X(f"{x_field}:Q", title=x_title)
    y = alt.Y(f"{y_field}:N", sort="-x", title=None)
    color = alt.Color(
        f"{x_field}:Q",
        scale=_qty_color_scale(),
        legend=alt.Legend(title="Urgencia (u.)"),
    )
    encoded = alt.Chart(df).encode(x=x, y=y, color=color, tooltip=tooltips)
    rules = encoded.mark_rule(strokeWidth=3)
    circles = encoded.mark_circle(size=180, opacity=0.95)
    if selectable_field:
        hit_df = df.copy()
        hit_df["_hit_max"] = float(df[x_field].max()) if not df.empty else 0.0
        hit = (
            alt.Chart(hit_df)
            .mark_bar(opacity=0.01, size=28)
            .encode(
                x=alt.X("_hit_max:Q", title=x_title),
                y=y,
                tooltip=tooltips,
            )
            .add_params(_point_param(selection_name, selectable_field))
        )
        # Hit layer last so the full row receives the click, not the thin rule.
        chart = rules + circles + hit
    else:
        chart = rules + circles
    return chart.properties(height=max(260, 32 * max(len(rows), 1)))


def histogram(
    rows: list[dict],
    x_field: str,
    x_title: str,
    y_field: str = "sku_count",
    y_title: str = "Productos",
    x_sort: list[str] | None = None,
    *,
    selectable_field: str | None = None,
    selection_name: str = "chart_select",
) -> alt.Chart:
    df = pd.DataFrame(rows)
    domain = x_sort or [str(r.get(x_field, "")) for r in rows]
    range_ = [COVERAGE_COLORS.get(str(b), "#546E7A") for b in domain]
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X(
                f"{x_field}:N",
                title=x_title,
                sort=x_sort or [],
                axis=alt.Axis(labelAngle=0),
            ),
            y=alt.Y(f"{y_field}:Q", title=y_title),
            color=alt.Color(
                f"{x_field}:N",
                scale=alt.Scale(domain=domain, range=range_),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip(f"{x_field}:N", title=x_title),
                alt.Tooltip(f"{y_field}:Q", title=y_title),
            ],
        )
        .properties(height=280)
    )
    if selectable_field:
        chart = chart.add_params(_point_param(selection_name, selectable_field))
    return chart


def _unwrap_scalar(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        return _unwrap_scalar(value[0]) if value else None
    if isinstance(value, dict):
        return None
    text = str(value).strip()
    return text or None


def _mapping_get(obj: Any, key: str) -> Any:
    getter = getattr(obj, "get", None)
    if callable(getter):
        return getter(key)
    return getattr(obj, key, None)


def selection_value(
    event: Any,
    field: str,
    *,
    selection_name: str = "chart_select",
) -> str | None:
    if not event:
        return None
    selection = _mapping_get(event, "selection")
    if selection is None:
        selection = getattr(event, "selection", None)
    if not selection:
        return None
    raw = _mapping_get(selection, selection_name)
    if not raw:
        items = getattr(selection, "items", None)
        if callable(items):
            for _, val in items():
                if val:
                    raw = val
                    break
    if not raw:
        return None
    if isinstance(raw, list):
        first = raw[0]
        if isinstance(first, dict):
            return _unwrap_scalar(first.get(field))
        return _unwrap_scalar(first)
    return _unwrap_scalar(_mapping_get(raw, field))
