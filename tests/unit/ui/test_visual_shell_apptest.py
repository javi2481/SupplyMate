"""AppTests for visual shell polish."""

from __future__ import annotations

from pathlib import Path

from ui.composition import copy as ui_copy
from ui.composition.kpi_policy import KpiCard


def test_visual_shell_copy_constants():
    from ui.threads.store import DEFAULT_TITLE

    assert ui_copy.SEARCH_PLACEHOLDER == "Buscar recortes"
    assert ui_copy.AI_READING_TOGGLE == "Lectura con IA"
    assert ui_copy.NEW_CHAT == "+ Nuevo recorte"
    assert DEFAULT_TITLE == "Nuevo chat"


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
    captions = [str(c.value) for c in at.caption]
    assert not any("sm-hero-title" in item for item in markdown)
    assert not any(ui_copy.APP_NAME in item for item in markdown)
    assert any(ui_copy.MODE_EXPLORE in item for item in captions + markdown)
    assert any(ui_copy.APP_TAGLINE in item for item in captions + markdown)


def test_theme_sidebar_primary_is_not_danger():
    from ui import theme

    assert "button[kind=\"primary\"]" in theme.CSS
    assert "background: var(--sm-primary-accent)" in theme.CSS
    assert ".block-container" in theme.CSS
    assert "max-width: 1150px" in theme.CSS
    primary_block = theme.CSS.split('button[kind="primary"]')[1].split("}")[0]
    assert "--sm-danger-accent" not in primary_block


def test_streamlit_floor_supports_bottom():
    text = Path(__file__).resolve().parents[3].joinpath("pyproject.toml").read_text(encoding="utf-8")
    assert "streamlit>=" in text
    # Floor must be at least 1.57 for public st.bottom; pin below next major.
    assert "streamlit>=1.57.0,<2" in text


def test_static_coverage_caption_matches_brand_blue_chart():
    text = Path(__file__).resolve().parents[3].joinpath("ui", "streamlit_app.py").read_text(
        encoding="utf-8"
    )
    assert "Rojo = pocos días de stock" not in text
    assert "Barras en azul de marca" in text


def test_merge_dashboard_requires_both_chart_series():
    text = Path(__file__).resolve().parents[3].joinpath("ui", "streamlit_app.py").read_text(
        encoding="utf-8"
    )
    assert 'dash.get("by_category") and dash.get("coverage")' in text


def test_kpi_card_escapes_html_payload():
    from ui import components

    markup = components._kpi_card(
        "<b>Productos</b>",
        "<script>1</script>",
        '"><img src=x onerror=alert(1)>',
        "hint <i>x</i>",
    )
    assert "<b>Productos</b>" not in markup
    assert "<script>" not in markup
    assert "&lt;b&gt;Productos&lt;/b&gt;" in markup
    assert "&lt;script&gt;" in markup
    # Attribute breakout must not leave a raw quote before the attacker payload.
    assert 'style="--sm-accent: &quot;' in markup
    assert '"><img' not in markup


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
    assert not any(
        item.strip() in ("<div class='sm-chart-card'>", '<div class="sm-chart-card">')
        for item in markdown
    )
    assert not any(item.strip() == "</div>" for item in markdown)
    assert any("Distribución de cobertura" in item for item in markdown)
    assert any("Click en un bucket para filtrar" in str(c.value) for c in at.caption)


def test_streamlit_app_renders_composer_shell(tmp_path, monkeypatch):
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("SUPPLYMATE_THREADS_PATH", str(tmp_path / "threads.json"))
    script = Path(__file__).resolve().parents[3] / "ui" / "streamlit_app.py"
    at = AppTest.from_file(str(script))
    at.session_state["pending_prompt"] = None
    at.session_state["live_list_active"] = False
    at.session_state["messages"] = [
        {"role": "assistant", "content": "Listo para explorar.", "mode": "error"}
    ]
    at.run(timeout=20)
    assert not at.exception
    markdown = [str(item.value) for item in at.markdown]
    assert not any(
        item.strip().startswith(("<div class='sm-composer", '<div class="sm-composer'))
        for item in markdown
    )
    assert not any(
        item.strip() in ("<div class='sm-panel'>", '<div class="sm-panel">')
        for item in markdown
    )
    assert len(at.chat_input) >= 1
    assert at.chat_input[0].placeholder == ui_copy.CHAT_PLACEHOLDER
