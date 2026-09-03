"""Lectura del recorte — explore insight and commit summary."""

from __future__ import annotations

import streamlit as st

from ui.composition import copy as ui_copy


def render_mode_badge(panel_mode: str) -> None:
    if panel_mode == "commit":
        st.markdown(
            f'<span class="sm-badge sm-badge-commit">{ui_copy.MODE_COMMIT}</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<span class="sm-badge sm-badge-explore">{ui_copy.MODE_EXPLORE}</span>',
            unsafe_allow_html=True,
        )


def render_analyst_card(
    *,
    panel_mode: str,
    evidence: str,
    insight: dict | None,
    commit_summary: dict | None,
    insight_source: str,
    analyst_enabled: bool,
) -> None:
    if not analyst_enabled:
        return

    st.markdown(f"### {ui_copy.ANALYST_TITLE}")
    st.caption(ui_copy.ANALYST_CAPTION)
    if insight_source == "fallback":
        st.caption("No pudimos generar una explicación con IA; el análisis numérico sigue disponible.")

    if panel_mode == "commit" and commit_summary:
        st.markdown(f"**{commit_summary.get('headline', 'Resumen OC')}**")
        st.markdown(commit_summary.get("oc_summary", ""))
        for item in commit_summary.get("top_priorities") or []:
            st.markdown(
                f"- **{item.get('product_name')}** · "
                f"{item.get('recommended_quantity')} u. — {item.get('reason', '')}"
            )
        for line in commit_summary.get("checklist") or []:
            st.caption(f"☑ {line}")
    elif insight:
        title = insight.get("panel_title") or "Recorte actual"
        st.markdown(f"**{title}**")
        if insight.get("summary"):
            st.markdown(insight["summary"])
        for bullet in insight.get("bullets") or []:
            st.markdown(f"- {bullet}")
        priorities = insight.get("purchase_priorities") or []
        if priorities:
            st.markdown("**Comprar primero (sugerido)**")
            for item in priorities:
                st.markdown(
                    f"- *Sugerido* **{item.get('product_name')}** · "
                    f"{item.get('recommended_quantity')} u. — {item.get('reason', '')}"
                )
        for hint in insight.get("navigation_hints") or []:
            st.caption(f"→ {hint}")
    else:
        st.markdown(evidence)


def render_suggested_questions(questions: list[str], *, key_prefix: str) -> None:
    if not questions:
        return
    st.markdown("**Preguntas sugeridas**")
    cols = st.columns(min(len(questions), 3))
    for i, q in enumerate(questions[:3]):
        if cols[i].button(q, key=f"{key_prefix}-sq-{i}"):
            st.session_state.pending_prompt = q
            st.rerun()


def render_exploration_timeline(events: list[dict]) -> None:
    if not events:
        return
    with st.expander("Historial de exploración", expanded=False):
        for i, ev in enumerate(events, 1):
            label = ev.get("label_human") or ev.get("value") or ev.get("action")
            st.caption(f"{i}. {label}")
