"""Altair charts for SupplyMate drill-down (static + selectable)."""

from __future__ import annotations

import altair as alt

from ui.theme import COVERAGE_COLORS


def _qty_color_scale() -> alt.Scale:
    return alt.Scale(scheme="orangered")


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
    tooltips = [
        alt.Tooltip(f"{y_field}:N", title=y_title),
        *(extra_tooltips or []),
        alt.Tooltip(f"{x_field}:Q", title=x_title),
    ]
    base = alt.Chart(alt.Data(values=rows)).encode(
        x=alt.X(f"{x_field}:Q", title=x_title),
        y=alt.Y(f"{y_field}:N", sort="-x", title=None),
        color=alt.Color(
            f"{x_field}:Q",
            scale=_qty_color_scale(),
            legend=alt.Legend(title="Urgencia (u.)"),
        ),
        tooltip=tooltips,
    )
    chart = base.mark_rule(strokeWidth=2) + base.mark_circle(size=110, opacity=0.95)
    chart = chart.properties(height=max(260, 32 * max(len(rows), 1)))
    if selectable_field:
        brush = alt.selection_point(name=selection_name, fields=[selectable_field])
        chart = chart.add_params(brush)
    return chart


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
    domain = x_sort or [str(r.get(x_field, "")) for r in rows]
    range_ = [COVERAGE_COLORS.get(str(b), "#546E7A") for b in domain]
    chart = (
        alt.Chart(alt.Data(values=rows))
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
        brush = alt.selection_point(name=selection_name, fields=[selectable_field])
        chart = chart.add_params(brush)
    return chart


def selection_value(
    event: dict | None,
    field: str,
    *,
    selection_name: str = "chart_select",
) -> str | None:
    if not event:
        return None
    selection = event.get("selection") or {}
    points = selection.get(selection_name) or []
    if not points:
        for key, val in selection.items():
            if isinstance(val, list) and val:
                points = val
                break
    if not points:
        return None
    point = points[0] if isinstance(points, list) else points
    if isinstance(point, dict):
        value = point.get(field)
        return str(value) if value is not None else None
    return None
