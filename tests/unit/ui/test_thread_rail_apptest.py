"""AppTest: ChatGPT-shaped sidebar rail (no HTTP)."""

from __future__ import annotations

from pathlib import Path

from app.core.models import AnalyticalScope
from ui.composition import copy as ui_copy
from ui.threads import ThreadStore


def _seed_store(path: Path, *, pinned: bool = False) -> ThreadStore:
    store = ThreadStore(path)
    store.upsert_session(
        "cabello",
        {
            "messages": [{"role": "user", "content": "¿Qué hay en cabello?"}],
            "analytical_scope": AnalyticalScope(categories=["Cuidado del Cabello"]).model_dump(),
            "panel_mode": "explore",
            "frozen_scope": None,
            "live_list_active": True,
            "slice_data": {"dashboard": {"skus": 10}},
            "analyze_data": None,
            "interaction_events": [],
            "root_skus": 10,
            "root_question": "¿Qué hay en cabello?",
            "highlight_calc": None,
            "guidance": None,
        },
    )
    store.upsert_session(
        "panales",
        {
            "messages": [{"role": "user", "content": "¿Qué hay en pañales?"}],
            "analytical_scope": AnalyticalScope(categories=["Pañales"], subcategories=["Bebé"]).model_dump(),
            "panel_mode": "explore",
            "frozen_scope": None,
            "live_list_active": True,
            "slice_data": {"dashboard": {"skus": 120}, "purchase_list": [{}] * 4},
            "analyze_data": None,
            "interaction_events": [],
            "root_skus": 120,
            "root_question": "¿Qué hay en pañales?",
            "highlight_calc": None,
            "guidance": None,
        },
    )
    if pinned:
        store.set_pinned("cabello", True)
    return store


def _rail_harness() -> None:
    import streamlit as st
    from pathlib import Path

    from ui import chrome
    from ui.threads import ThreadStore, prepare_new_chat, switch_thread

    store = ThreadStore(Path(st.session_state["thread_store_path"]))
    if "active_thread_id" not in st.session_state:
        st.session_state.active_thread_id = None
    with st.sidebar:
        action = chrome.render_thread_rail(
            store,
            active_id=st.session_state.get("active_thread_id"),
        )
        if action is None:
            pass
        elif action.kind == "new_chat":
            prepare_new_chat(store, st.session_state)
        elif action.kind == "select" and action.thread_id:
            switch_thread(store, st.session_state, action.thread_id)
        elif action.kind == "pin" and action.thread_id:
            store.set_pinned(action.thread_id, True)
        elif action.kind == "unpin" and action.thread_id:
            store.set_pinned(action.thread_id, False)
    st.caption("harness-ok")


def test_sidebar_order_nuevo_fijados_historial(tmp_path: Path):
    from streamlit.testing.v1 import AppTest

    path = tmp_path / "threads.json"
    _seed_store(path)
    at = AppTest.from_function(_rail_harness)
    at.session_state["thread_store_path"] = str(path)
    at.run(timeout=15)
    assert not at.exception
    assert at.button[0].label == ui_copy.NEW_CHAT
    markdown = [str(item.value) for item in at.markdown]
    fijados = next(i for i, m in enumerate(markdown) if ui_copy.PINNED_SECTION in m)
    historial = next(i for i, m in enumerate(markdown) if ui_copy.HISTORY_SECTION in m)
    assert fijados < historial
    assert not any(b.label == "Limpiar chat" for b in at.button)


def test_empty_fijados_caption_no_limpiar_chat(tmp_path: Path):
    from streamlit.testing.v1 import AppTest

    path = tmp_path / "threads.json"
    _seed_store(path, pinned=False)
    at = AppTest.from_function(_rail_harness)
    at.session_state["thread_store_path"] = str(path)
    at.run(timeout=15)
    assert not at.exception
    captions = [str(c.value) for c in at.caption]
    markdown = [str(m.value) for m in at.markdown]
    assert ui_copy.PINNED_EMPTY in captions or any(ui_copy.PINNED_EMPTY in m for m in markdown)
    assert not any(b.label == "Limpiar chat" for b in at.button)


def test_streamlit_app_sidebar_uses_nuevo_chat(tmp_path: Path, monkeypatch):
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("SUPPLYMATE_THREADS_PATH", str(tmp_path / "threads.json"))
    script = Path(__file__).resolve().parents[3] / "ui" / "streamlit_app.py"
    at = AppTest.from_file(str(script))
    at.run(timeout=20)
    assert not at.exception
    labels = [b.label for b in at.button]
    assert ui_copy.NEW_CHAT in labels
    assert "Limpiar chat" not in labels
    markdown = [str(item.value) for item in at.markdown]
    assert any(ui_copy.PINNED_SECTION in m for m in markdown)
    assert any(ui_copy.HISTORY_SECTION in m for m in markdown)


def test_selecting_history_row_restores_messages_and_scope(tmp_path: Path):
    from streamlit.testing.v1 import AppTest

    path = tmp_path / "threads.json"
    _seed_store(path)
    at = AppTest.from_function(_rail_harness)
    at.session_state["thread_store_path"] = str(path)
    at.run(timeout=15)
    assert not at.exception
    # El título se muestra como markdown; el botón de selección usa key "hist-open-cabello"
    target = at.button(key="hist-open-cabello")
    assert target is not None, "No se encontró el botón del hilo cabello"
    target.click().run(timeout=15)
    assert not at.exception
    messages = at.session_state["messages"]
    assert messages[0]["content"] == "¿Qué hay en cabello?"
    assert at.session_state["analytical_scope"]["categories"] == ["Cuidado del Cabello"]
    assert at.session_state["live_list_active"] is True


def test_sidebar_search_filters_thread_rows(tmp_path: Path):
    from streamlit.testing.v1 import AppTest

    path = tmp_path / "threads.json"
    _seed_store(path, pinned=True)
    at = AppTest.from_function(_rail_harness)
    at.session_state["thread_store_path"] = str(path)
    at.run(timeout=15)
    assert not at.exception
    search = at.text_input(key="rail-search")
    assert search is not None, "No se encontró el input de búsqueda"
    search.set_value("bebé").run(timeout=15)
    assert not at.exception
    labels = [b.label for b in at.button]
    assert "Pañales · Bebé" in labels
    assert "Cuidado del Cabello" not in labels


def test_sidebar_search_shows_no_results_message(tmp_path: Path):
    from streamlit.testing.v1 import AppTest

    path = tmp_path / "threads.json"
    _seed_store(path, pinned=True)
    at = AppTest.from_function(_rail_harness)
    at.session_state["thread_store_path"] = str(path)
    at.run(timeout=15)
    assert not at.exception
    search = at.text_input(key="rail-search")
    search.set_value("inexistente").run(timeout=15)
    assert not at.exception
    markdown = [str(item.value) for item in at.markdown]
    assert any(ui_copy.SEARCH_NO_RESULTS in item for item in markdown)
    assert not any(ui_copy.PINNED_SECTION in item for item in markdown)
