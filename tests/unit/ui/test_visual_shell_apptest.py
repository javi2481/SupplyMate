"""AppTests for visual shell polish."""

from __future__ import annotations

from ui.composition import copy as ui_copy
from ui.composition.kpi_policy import KpiCard


def test_visual_shell_copy_constants():
    assert ui_copy.SEARCH_PLACEHOLDER == "Buscar recortes"
    assert ui_copy.AI_READING_TOGGLE == "Lectura con IA"


def _kpi_shell_harness() -> None:
    from ui import components
    from ui.composition.kpi_policy import KpiCard

    components.inject_theme()
    components.render_kpi_cards(
        [
            KpiCard(
                "Productos",
                "2430",
                "#90CAF9",
                "SKUs en el recorte actual",
                icon_key="products",
            )
        ]
    )


def test_visual_shell_kpi_render_includes_icon_markup():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_function(_kpi_shell_harness)
    at.run(timeout=15)
    assert not at.exception
    markdown = [str(item.value) for item in at.markdown]
    assert any("sm-kpi-icon" in item for item in markdown)
    assert any("--sm-accent" in item for item in markdown)


def _analyst_toggle_harness() -> None:
    import streamlit as st

    from ui import analyst
    from ui.composition import copy as ui_copy

    if "analyst_enabled" not in st.session_state:
        st.session_state.analyst_enabled = True
    with st.sidebar:
        st.toggle(
            ui_copy.AI_READING_TOGGLE,
            key="analyst_enabled",
        )
    analyst.render_analyst_card(
        panel_mode="explore",
        evidence="Por qué ves esto",
        insight={"summary": "Resumen"},
        commit_summary=None,
        insight_source="fallback",
        analyst_enabled=st.session_state.analyst_enabled,
    )


def test_analyst_toggle_hides_lectura_del_recorte():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_function(_analyst_toggle_harness)
    at.run(timeout=15)
    assert not at.exception
    toggle = at.toggle[0]
    assert toggle.label == ui_copy.AI_READING_TOGGLE
    toggle.set_value(False).run(timeout=15)
    assert not at.exception
    markdown = [str(item.value) for item in at.markdown]
    assert not any(ui_copy.ANALYST_TITLE in item for item in markdown)


def _header_harness() -> None:
    from ui import chrome, components

    components.inject_theme()
    chrome.render_header("explore", live=True)


def test_visual_shell_header_uses_hero_markup():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_function(_header_harness)
    at.run(timeout=15)
    assert not at.exception
    markdown = [str(item.value) for item in at.markdown]
    assert any("sm-hero-title" in item for item in markdown)
    assert any(ui_copy.APP_NAME in item for item in markdown)
    assert any(ui_copy.APP_TAGLINE in item for item in markdown)
    assert any(ui_copy.MODE_EXPLORE in item for item in markdown)


def _chart_card_harness() -> None:
    from ui import components

    components.inject_theme()
    components.render_chart_card(
        "Distribución de cobertura",
        caption="Click en un bucket para filtrar",
        body=lambda: None,
    )


def test_visual_shell_chart_card_wrapper_markup():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_function(_chart_card_harness)
    at.run(timeout=15)
    assert not at.exception
    markdown = [str(item.value) for item in at.markdown]
    assert any("sm-chart-card" in item for item in markdown)
    assert any("Distribución de cobertura" in item for item in markdown)


def test_streamlit_app_renders_composer_shell(tmp_path, monkeypatch):
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("SUPPLYMATE_THREADS_PATH", str(tmp_path / "threads.json"))
    script = Path(__file__).resolve().parents[3] / "ui" / "streamlit_app.py"
    at = AppTest.from_file(str(script))
    at.session_state["pending_prompt"] = None
    at.session_state["live_list_active"] = False
    at.run(timeout=20)
    assert not at.exception
    markdown = [str(item.value) for item in at.markdown]
    assert any("sm-composer" in item for item in markdown)
