"""Commit focus layout — quiet OC confirmation."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from app.core.models import AnalyticalScope
from ui import analyst, components
from ui.composition import copy as ui_copy
from ui.composition.kpi_policy import commit_kpi_cards
from ui.composition.scope_label import compact_scope_line
from ui.composition.table_policy import EXPLORE_COLUMNS, build_explore_rows


def render_commit_panel(
    *,
    scope: AnalyticalScope,
    slice_data: dict,
    analyze_data: dict,
    analyst_enabled: bool,
    csv_bytes: bytes | None,
    on_exit: Callable[[], None] | None = None,
    on_reanalyze: Callable[[], None] | None = None,
) -> None:
    purchase_list = slice_data.get("purchase_list") or []
    evidence = slice_data.get("evidence") or ""
    commit_summary = analyze_data.get("commit_summary")
    insight_source = analyze_data.get("insight_source", "fallback")

    st.markdown(f"### OC propuesta")
    st.caption(compact_scope_line(scope))
    components.render_kpi_cards(commit_kpi_cards(purchase_list))
    components.render_oc_summary(purchase_list)

    analyst.render_analyst_card(
        panel_mode="commit",
        evidence=evidence,
        insight=None,
        commit_summary=commit_summary,
        insight_source=insight_source,
        analyst_enabled=analyst_enabled,
    )

    if purchase_list:
        import pandas as pd

        df = pd.DataFrame(build_explore_rows(purchase_list), columns=EXPLORE_COLUMNS)
        st.dataframe(df, width="stretch", hide_index=True, column_order=EXPLORE_COLUMNS)

    if csv_bytes:
        st.download_button(
            f"{ui_copy.EXPORT_PREFIX} ({len(purchase_list)} SKUs)",
            data=csv_bytes,
            file_name="purchase_order.csv",
            mime="text/csv",
            key=f"dl-slice-commit",
            type="primary",
        )
    if st.button(ui_copy.BACK_TO_EXPLORE, key="exit_commit"):
        if on_exit:
            on_exit()
        st.rerun()
    if analyst_enabled and on_reanalyze:
        if st.button("Reconfirmar con IA", key="reanalyze_commit"):
            on_reanalyze()
            st.rerun()
