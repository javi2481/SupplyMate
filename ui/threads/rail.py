"""ChatGPT-shaped thread rail — fiel al mockup aprobado."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import streamlit as st

from ui.composition import copy as ui_copy
from ui.threads.store import ThreadStore, group_history_by_day

RailKind = Literal["new_chat", "select", "pin", "unpin"]


@dataclass(frozen=True)
class RailAction:
    kind: RailKind
    thread_id: str | None = None


def render_thread_rail(store: ThreadStore, *, active_id: str | None) -> RailAction | None:
    clicked: RailAction | None = None

    # Nuevo chat — ancho completo, botón primario
    if st.button(ui_copy.NEW_CHAT, key="rail-new-chat", use_container_width=True, type="primary"):
        clicked = RailAction("new_chat")

    # ── Fijados ──────────────────────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:0.72rem;font-weight:600;letter-spacing:.06em;"
        "opacity:.55;text-transform:uppercase;margin-top:14px;margin-bottom:4px'>"
        f"{ui_copy.PINNED_SECTION}</div>",
        unsafe_allow_html=True,
    )
    pinned = store.pinned_threads()
    if not pinned:
        st.caption(ui_copy.PINNED_EMPTY)
    else:
        action = _render_thread_rows(pinned, active_id=active_id, prefix="pin")
        if action is not None:
            clicked = action

    # ── Historial de chats ───────────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:0.72rem;font-weight:600;letter-spacing:.06em;"
        "opacity:.55;text-transform:uppercase;margin-top:14px;margin-bottom:4px'>"
        f"{ui_copy.HISTORY_SECTION}</div>",
        unsafe_allow_html=True,
    )
    groups = group_history_by_day(store.history_threads())
    for day_label, threads in groups:
        st.markdown(
            f"<div style='font-size:0.72rem;opacity:.45;margin:6px 0 2px'>"
            f"{day_label}</div>",
            unsafe_allow_html=True,
        )
        action = _render_thread_rows(threads, active_id=active_id, prefix="hist")
        if action is not None:
            clicked = action

    return clicked


def _render_thread_rows(threads, *, active_id: str | None, prefix: str) -> RailAction | None:
    clicked: RailAction | None = None
    for thread in threads:
        is_active = thread.id == active_id
        active_style = (
            "border-left:3px solid var(--primary-color,#e05252);padding-left:8px;border-radius:4px;"
            if is_active
            else "border-left:3px solid transparent;padding-left:8px;"
        )
        # Bloque título + subtítulo: si el botón invisible ocupa todo el ancho,
        # usamos un contenedor con markdown + button superpuesto via columnas
        title_html = (
            f"<div style='font-weight:600;font-size:0.9rem;line-height:1.3;{active_style}'>"
            f"{thread.title}</div>"
        )
        sub_html = ""
        if thread.subtitle:
            sub_html = (
                f"<div style='font-size:0.75rem;opacity:.55;padding-left:11px'>"
                f"{thread.subtitle}</div>"
            )
        info_col, pin_col = st.columns([7, 1])
        with info_col:
            st.markdown(title_html + sub_html, unsafe_allow_html=True)
            if st.button(
                "·",
                key=f"{prefix}-open-{thread.id}",
                help=thread.title,
                use_container_width=True,
            ):
                clicked = RailAction("select", thread.id)
        with pin_col:
            icon = "📌" if not thread.pinned else "✕"
            help_text = ui_copy.PIN_THREAD if not thread.pinned else ui_copy.UNPIN_THREAD
            if st.button(icon, key=f"{prefix}-toggle-{thread.id}", help=help_text):
                clicked = RailAction("unpin" if thread.pinned else "pin", thread.id)
    return clicked
