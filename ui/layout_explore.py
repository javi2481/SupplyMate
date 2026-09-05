"""Explore focus layout — conversation-adjacent evidence."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import altair as alt
import streamlit as st

from app.core.models import AnalyticalScope
from app.services import dashboard as dash_svc
from ui import charts, components
from ui.composition import copy as ui_copy
from ui.composition import kpi_actions
from ui.composition.kpi_policy import explore_kpi_cards
from ui.composition.next_step import NextStep, NextStepOption
from ui.composition.scope_label import compact_scope_line, scope_has_filters, sku_count_caption


def _render_kpi_controls(
    dash: dict,
    *,
    on_kpi: Callable[[str], None] | None,
) -> None:
    cards = explore_kpi_cards(dash)
    actions = [
        kpi_actions.KPI_PRODUCTS,
        kpi_actions.KPI_UNDERSTOCK,
        kpi_actions.KPI_STOCKOUT_RISK,
        kpi_actions.KPI_COVERAGE,
    ]
    cols = st.columns(len(cards))
    for col, card, action in zip(cols, cards, actions, strict=False):
        with col:
            if action == kpi_actions.KPI_COVERAGE or on_kpi is None:
                components.render_kpi_cards([card])
            else:
                label = f"{card.label}\n{card.value}"
                if st.button(label, key=f"kpi_ctrl_{action}", use_container_width=True):
                    on_kpi(action)
                    st.rerun()


def _render_context_bar(
    *,
    scope: AnalyticalScope,
    root_skus: int | None,
    current_skus: int | None,
    can_go_back: bool,
    on_back: Callable[[], None] | None,
    on_reset: Callable[[], None] | None,
) -> None:
    show = scope_has_filters(scope) or can_go_back
    if not show:
        return
    cols = st.columns([1, 4, 1])
    with cols[0]:
        if st.button(
            f"← {ui_copy.VOLVER_SCOPE}",
            key="scope_back",
            disabled=not can_go_back or on_back is None,
        ):
            if on_back:
                on_back()
                st.rerun()
    with cols[1]:
        st.markdown(compact_scope_line(scope))
        caption = sku_count_caption(
            root_skus, current_skus if isinstance(current_skus, int) else None
        )
        if caption:
            st.caption(caption)
    with cols[2]:
        if on_reset and st.button(ui_copy.CLEAR_SCOPE, key="reset_scope"):
            on_reset()
            st.rerun()


def render_explore_panel(
    *,
    scope: AnalyticalScope,
    slice_data: dict,
    analyze_data: dict,
    next_step: NextStep,
    interaction_events: list[dict],
    highlight_calc: dict | None,
    analyst_enabled: bool,
    root_skus: int | None,
    on_option: Callable[[NextStepOption], None] | None = None,
    on_prompt: Callable[[str], None] | None = None,
    on_reset: Callable[[], None] | None = None,
    on_back: Callable[[], None] | None = None,
    can_go_back: bool = False,
    on_category: Callable[[str], None] | None = None,
    on_coverage: Callable[[str], None] | None = None,
    on_sku: Callable[[str], None] | None = None,
    on_kpi: Callable[[str], None] | None = None,
    on_enter_commit: Callable[[], None] | None = None,
    table_selection_sku: Callable[[Any, list[dict]], str | None] | None = None,
    render_calculation: Callable[[dict], None] | None = None,
) -> None:
    del analyze_data, next_step, interaction_events
    del analyst_enabled, on_option, on_prompt, on_enter_commit
    del table_selection_sku
    # on_sku / on_kpi / highlight_calc / render_calculation used by later slices

    dash = slice_data.get("dashboard") or {}
    category_rows = dash.get("by_category") or []
    coverage_rows = dash.get("coverage") or []
    current_skus = dash.get("skus")
    show_sku = bool(scope.highlight_product_id and highlight_calc)

    _render_context_bar(
        scope=scope,
        root_skus=root_skus,
        current_skus=current_skus if isinstance(current_skus, int) else None,
        can_go_back=can_go_back,
        on_back=on_back,
        on_reset=on_reset,
    )

    if show_sku:
        _render_sku_slot(highlight_calc or {}, render_calculation=render_calculation)
        return

    _render_kpi_controls(dash, on_kpi=on_kpi)
    del on_sku

    left, right = st.columns(2)
    with left:
        def _render_category_chart() -> None:
            if category_rows:
                cat_chart = charts.lollipop(
                    category_rows,
                    "category",
                    "Categoría",
                    extra_tooltips=[alt.Tooltip("sku_count:Q", title="Productos")],
                    selectable_field="category",
                    selection_name="category_select",
                    selected_values=scope.categories,
                )
                cat_event = st.altair_chart(
                    cat_chart,
                    on_select="rerun",
                    selection_mode="category_select",
                    key="live_category_chart",
                    width="stretch",
                )
                cat_value = charts.selection_value(
                    cat_event, "category", selection_name="category_select"
                )
                if cat_value and on_category and cat_value not in scope.categories:
                    on_category(cat_value)
                    st.rerun()

        components.render_chart_card(
            ui_copy.CHART_CATEGORY_TITLE,
            caption=ui_copy.CHART_CATEGORY_SUBTITLE,
            body=_render_category_chart,
        )
    with right:
        def _render_coverage_chart() -> None:
            if coverage_rows:
                cov_chart = charts.histogram(
                    coverage_rows,
                    "bucket",
                    ui_copy.CHART_COVERAGE_AXIS,
                    x_sort=list(dash_svc.COVERAGE_ORDER),
                    selectable_field="bucket",
                    selection_name="coverage_select",
                    selected_values=scope.coverage_buckets,
                )
                cov_event = st.altair_chart(
                    cov_chart,
                    on_select="rerun",
                    selection_mode="coverage_select",
                    key="live_coverage_chart",
                    width="stretch",
                )
                bucket_value = charts.selection_value(
                    cov_event, "bucket", selection_name="coverage_select"
                )
                if bucket_value and on_coverage and bucket_value not in scope.coverage_buckets:
                    on_coverage(bucket_value)
                    st.rerun()

        components.render_chart_card(
            ui_copy.CHART_COVERAGE_TITLE,
            caption=ui_copy.CHART_COVERAGE_SUBTITLE,
            body=_render_coverage_chart,
        )


def _render_sku_slot(
    payload: dict,
    *,
    render_calculation: Callable[[dict], None] | None,
) -> None:
    """SKU detail card inside live Explore Answer Surface."""
    calc = payload.get("calculation") if isinstance(payload.get("calculation"), dict) else payload
    ctx = payload.get("context") if isinstance(payload.get("context"), dict) else {}
    name = (
        payload.get("product_name")
        or payload.get("name")
        or "Producto"
    )
    qty = payload.get("recommended_quantity")
    if qty is None:
        qty = calc.get("recommended_quantity", 0) if isinstance(calc, dict) else 0
    stock = ctx.get("current_stock")
    if stock is None and isinstance(calc, dict):
        stock = calc.get("current_stock", "—")
    demand = None
    if isinstance(calc, dict):
        demand = calc.get("average_daily_demand")
    rop = ctx.get("reorder_point")
    if rop is None and isinstance(ctx.get("inventory"), dict):
        rop = ctx["inventory"].get("reorder_point")

    st.markdown(f"**{name}**")
    st.metric(ui_copy.BUY_LABEL, f"{qty} unidades")
    cols = st.columns(3)
    cols[0].metric("Stock", stock if stock is not None else "—")
    cols[1].metric(
        "Demanda diaria",
        round(demand, 1) if isinstance(demand, (int, float)) else "—",
    )
    cols[2].metric("Punto de reorden", rop if rop is not None else "—")
    if render_calculation and isinstance(calc, dict):
        render_calculation(calc)
