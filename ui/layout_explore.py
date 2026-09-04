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
from ui.composition.kpi_policy import explore_kpi_cards
from ui.composition.next_step import NextStep, NextStepOption
from ui.composition.scope_label import compact_scope_line, scope_has_filters, sku_count_caption


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
    on_category: Callable[[str], None] | None = None,
    on_coverage: Callable[[str], None] | None = None,
    on_sku: Callable[[str], None] | None = None,
    on_enter_commit: Callable[[], None] | None = None,
    table_selection_sku: Callable[[Any, list[dict]], str | None] | None = None,
    render_calculation: Callable[[dict], None] | None = None,
) -> None:
    del analyze_data, next_step, interaction_events, highlight_calc
    del analyst_enabled, on_option, on_prompt, on_sku, on_enter_commit
    del table_selection_sku, render_calculation

    dash = slice_data.get("dashboard") or {}
    category_rows = dash.get("by_category") or []
    coverage_rows = dash.get("coverage") or []

    if scope_has_filters(scope):
        st.markdown(compact_scope_line(scope))
        current_skus = dash.get("skus")
        caption = sku_count_caption(root_skus, current_skus if isinstance(current_skus, int) else None)
        if caption:
            st.caption(caption)
        if on_reset and st.button(ui_copy.CLEAR_SCOPE, key="reset_scope"):
            on_reset()
            st.rerun()

    components.render_kpi_cards(explore_kpi_cards(dash))

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
