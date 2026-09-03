"""Explore focus layout — conversation-adjacent evidence."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import altair as alt
import streamlit as st

from app.core.models import AnalyticalScope
from app.services import dashboard as dash_svc
from app.services import metrics
from app.services import scope as scope_svc
from ui import analyst, charts, chrome, components
from ui.composition import copy as ui_copy
from ui.composition.kpi_policy import explore_kpi_cards
from ui.composition.next_step import NextStep, NextStepOption, split_next_step_around_charts
from ui.composition.scope_label import compact_scope_line, sku_count_caption


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
    dash = slice_data.get("dashboard") or {}
    purchase_list = slice_data.get("purchase_list") or []
    evidence = slice_data.get("evidence") or ""
    insight = analyze_data.get("insight")
    insight_source = analyze_data.get("insight_source", "fallback")
    category_rows = dash.get("by_category") or []
    coverage_rows = dash.get("coverage") or []
    before_step, after_step = split_next_step_around_charts(
        next_step,
        has_category_chart=bool(category_rows),
        has_coverage_chart=bool(coverage_rows),
    )
    ns_key = f"ns-{scope_svc.cache_key(scope)}"

    st.markdown(compact_scope_line(scope))
    current_skus = dash.get("skus")
    caption = sku_count_caption(root_skus, current_skus if isinstance(current_skus, int) else None)
    if caption:
        st.caption(caption)
    if on_reset:
        if st.button(ui_copy.CLEAR_SCOPE, key="reset_scope"):
            on_reset()
            st.rerun()

    components.render_kpi_cards(explore_kpi_cards(dash))

    st.markdown(f"### {ui_copy.NEXT_STEP_TITLE}")
    if not before_step.question and not before_step.primary:
        st.caption(ui_copy.CHART_REFINE_HINT)
    chrome.render_next_step(
        before_step,
        key_prefix=f"{ns_key}-b",
        on_option=on_option,
        on_prompt=on_prompt,
        show_title=False,
    )

    left, right = st.columns(2)
    with left:
        st.markdown(f"**{metrics.LABEL_RECOMMENDED_QTY} por categoría**")
        st.caption("Click en una fila del gráfico para recortar")
        if category_rows:
            cat_chart = charts.lollipop(
                category_rows,
                "category",
                "Categoría",
                extra_tooltips=[alt.Tooltip("sku_count:Q", title="Productos")],
                selectable_field="category",
                selection_name="category_select",
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
    with right:
        st.markdown(f"**Distribución de {metrics.LABEL_COVERAGE}**")
        st.caption("Click en un bucket para filtrar")
        if coverage_rows:
            cov_chart = charts.histogram(
                coverage_rows,
                "bucket",
                metrics.LABEL_COVERAGE,
                x_sort=list(dash_svc.COVERAGE_ORDER),
                selectable_field="bucket",
                selection_name="coverage_select",
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

    chrome.render_next_step(
        after_step,
        key_prefix=f"{ns_key}-a",
        on_option=on_option,
        on_prompt=on_prompt,
        show_title=False,
    )

    if not purchase_list:
        st.warning("Ningún producto en este recorte. Quitá un filtro o usá **Limpiar**.")
    else:
        components.render_oc_summary(purchase_list)
        st.caption("Click en una fila para ver **Cómo se calculó**")
        table_event = components.render_explore_table(
            purchase_list,
            table_key="live_purchase_table",
            selectable=True,
        )
        if table_selection_sku and on_sku:
            sku = table_selection_sku(table_event, purchase_list)
            if sku and sku != scope.highlight_product_id:
                on_sku(sku)
                st.rerun()

    if highlight_calc and scope.highlight_product_id:
        st.markdown("---")
        st.markdown(f"### {highlight_calc.get('product_name', scope.highlight_product_id)}")
        cols = st.columns(3)
        cols[0].metric(
            metrics.LABEL_RECOMMENDED_QTY,
            highlight_calc.get("recommended_quantity", 0),
        )
        ctx = highlight_calc.get("context") or {}
        cols[1].metric("Stock actual", ctx.get("current_stock", "—"))
        cols[2].metric(metrics.LABEL_REORDER_POINT, ctx.get("reorder_point", "—"))
        if render_calculation:
            render_calculation(highlight_calc.get("calculation") or {})

    analyst.render_analyst_card(
        panel_mode="explore",
        evidence=evidence,
        insight=insight,
        commit_summary=None,
        insight_source=insight_source,
        analyst_enabled=analyst_enabled,
    )
    analyst.render_exploration_timeline(interaction_events)

    has_draft = any(
        opt.guidance_chip and opt.guidance_chip.get("action") == "draft_oc"
        for opt in next_step.primary
    )
    if not has_draft:
        if st.button(ui_copy.ENTER_COMMIT, type="primary", key="enter_commit"):
            if on_enter_commit:
                on_enter_commit()
            st.rerun()
