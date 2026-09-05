"""Altair charts for SupplyMate drill-down (static + selectable)."""

from __future__ import annotations

from collections.abc import Collection
from typing import Any

import altair as alt
import pandas as pd

from ui.theme import SHELL_TOKENS


def _brand_blue() -> str:
    return SHELL_TOKENS["primary_accent"]


def _point_param(
    selection_name: str,
    field: str,
    *,
    nearest: bool = False,
) -> alt.Parameter:
    return alt.selection_point(
        name=selection_name,
        fields=[field],
        nearest=nearest,
        toggle=False,
    )


def _with_selected_flag(
    df: pd.DataFrame,
    field: str,
    selected_values: Collection[str] | None,
) -> pd.DataFrame:
    out = df.copy()
    if selected_values:
        chosen = set(selected_values)
        out["_selected"] = out[field].isin(chosen)
    else:
        out["_selected"] = True
    return out


def _opacity_encoding() -> alt.Opacity:
    return alt.Opacity(
        "_selected:N",
        scale=alt.Scale(domain=[True, False], range=[0.95, 0.35]),
        legend=None,
    )


def _stroke_width_encoding() -> alt.StrokeWidth:
    return alt.StrokeWidth(
        "_selected:N",
        scale=alt.Scale(domain=[True, False], range=[5, 2]),
        legend=None,
    )


def _point_size_encoding() -> alt.Size:
    return alt.Size(
        "_selected:N",
        scale=alt.Scale(domain=[True, False], range=[280, 110]),
        legend=None,
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
    selected_values: Collection[str] | None = None,
) -> alt.Chart:
    df = _with_selected_flag(pd.DataFrame(rows), y_field, selected_values)
    tooltips = [
        alt.Tooltip(f"{y_field}:N", title=y_title),
        *(extra_tooltips or []),
        alt.Tooltip(f"{x_field}:Q", title=x_title),
    ]
    x = alt.X(f"{x_field}:Q", title=x_title)
    y = alt.Y(f"{y_field}:N", sort="-x", title=None)
    brand = _brand_blue()
    base = alt.Chart(df).encode(
        x=x,
        y=y,
        opacity=_opacity_encoding(),
        tooltip=tooltips,
    )
    rules = base.mark_rule(color=brand).encode(strokeWidth=_stroke_width_encoding())
    circles = base.mark_circle(color=brand).encode(size=_point_size_encoding())
    labels = base.mark_text(
        align="left",
        dx=8,
        fontSize=11,
        color=brand,
    ).encode(text=alt.Text(f"{x_field}:Q", format=",.0f"))
    if selectable_field:
        hit_df = df.copy()
        hit_df["_hit_zero"] = 0.0
        hit_df["_hit_max"] = float(df[x_field].max()) if not df.empty else 0.0
        hit = (
            alt.Chart(hit_df)
            .mark_rect(fillOpacity=0)
            .encode(
                y=y,
                x=alt.X("_hit_zero:Q", title=x_title),
                x2=alt.X2("_hit_max:Q"),
                tooltip=tooltips,
            )
            .add_params(
                _point_param(selection_name, selectable_field, nearest=False)
            )
        )
        chart = rules + circles + labels + hit
    else:
        chart = rules + circles + labels
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
    selected_values: Collection[str] | None = None,
) -> alt.Chart:
    df = _with_selected_flag(pd.DataFrame(rows), x_field, selected_values)
    brand = _brand_blue()
    base = (
        alt.Chart(df)
        .encode(
            x=alt.X(
                f"{x_field}:N",
                title=x_title,
                sort=x_sort or [],
                axis=alt.Axis(labelAngle=0),
            ),
            y=alt.Y(f"{y_field}:Q", title=y_title),
            opacity=_opacity_encoding(),
            tooltip=[
                alt.Tooltip(f"{x_field}:N", title=x_title),
                alt.Tooltip(f"{y_field}:Q", title=y_title),
            ],
        )
        .properties(height=280)
    )
    bars = base.mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        color=alt.value(brand),
    )
    labels = base.mark_text(
        dy=-8,
        fontSize=11,
        color=brand,
    ).encode(text=alt.Text(f"{y_field}:Q", format=",.0f"))
    chart = bars + labels
    if selectable_field:
        # nearest=True on bars can leave an empty Vega embed in Streamlit columns.
        chart = chart.add_params(
            _point_param(selection_name, selectable_field, nearest=False)
        )
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
