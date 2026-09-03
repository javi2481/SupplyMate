"""ChatGPT-shaped thread rail — alineado al mockup visual."""

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


def render_thread_rail(
    store: ThreadStore,
    *,
    active_id: str | None,
) -> RailAction | None:
    clicked: RailAction | None = None

    if st.button(
        ui_copy.NEW_CHAT,
        key="rail-new-chat",
        use_container_width=True,
        type="primary",
    ):
        clicked = RailAction("new_chat")

    query = st.text_input(
        ui_copy.SEARCH_PLACEHOLDER,
        key="rail-search",
        placeholder=ui_copy.SEARCH_PLACEHOLDER,
        label_visibility="collapsed",
    ).strip()
    matched = store.search(query) if query else None
    matches = {thread.id for thread in matched} if matched is not None else None

    if query and not matched:
        st.markdown(
            f"<p class='rail-empty'>{ui_copy.SEARCH_NO_RESULTS}</p>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"<p class='rail-section'>{ui_copy.PINNED_SECTION}</p>", unsafe_allow_html=True)
        pinned = store.pinned_threads()
        if matches is not None:
            pinned = [thread for thread in pinned if thread.id in matches]
        if not pinned:
            st.markdown(f"<p class='rail-empty'>{ui_copy.PINNED_EMPTY}</p>", unsafe_allow_html=True)
        else:
            action = _render_thread_rows(pinned, active_id=active_id, prefix="pin")
            if action is not None:
                clicked = action

        st.markdown(
            f"<p class='rail-section'>{ui_copy.HISTORY_SECTION}</p>",
            unsafe_allow_html=True,
        )
        history = store.history_threads()
        if matches is not None:
            history = [thread for thread in history if thread.id in matches]
        groups = group_history_by_day(history)
        if not groups:
            st.markdown("<p class='rail-empty'>Sin chats recientes</p>", unsafe_allow_html=True)
        for day_label, threads in groups:
            st.markdown(f"<p class='rail-day'>{day_label}</p>", unsafe_allow_html=True)
            action = _render_thread_rows(threads, active_id=active_id, prefix="hist")
            if action is not None:
                clicked = action

    if active_id:
        active = store.get(active_id)
        if active is not None:
            if active.pinned:
                if st.button(
                    ui_copy.UNPIN_THREAD,
                    key="rail-unpin-active",
                    use_container_width=True,
                ):
                    clicked = RailAction("unpin", active_id)
            else:
                if st.button(
                    ui_copy.PIN_THREAD,
                    key="rail-pin-active",
                    use_container_width=True,
                ):
                    clicked = RailAction("pin", active_id)

    st.markdown(
        f"<div class='rail-footer'>{ui_copy.APP_NAME}</div>",
        unsafe_allow_html=True,
    )
    st.toggle(ui_copy.AI_READING_TOGGLE, key="analyst_enabled")
    return clicked


def _render_thread_rows(threads, *, active_id: str | None, prefix: str) -> RailAction | None:
    clicked: RailAction | None = None
    for thread in threads:
        is_active = thread.id == active_id
        row_class = "rail-row rail-row-active" if is_active else "rail-row"
        st.markdown(f"<div class='{row_class}'>", unsafe_allow_html=True)
        if st.button(
            thread.title,
            key=f"{prefix}-open-{thread.id}",
            use_container_width=True,
            type="secondary",
        ):
            clicked = RailAction("select", thread.id)
        if thread.subtitle:
            st.markdown(
                f"<p class='rail-subtitle'>{thread.subtitle}</p>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
    return clicked
