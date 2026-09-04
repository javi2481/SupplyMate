"""AppTest harness for explore next-step hierarchy (no HTTP)."""

from __future__ import annotations


def _explore_harness() -> None:
    import streamlit as st
    from app.core.models import AnalyticalScope, GuidanceChip, GuidanceDecision, SuggestedFilter
    from ui import components
    from ui.composition.next_step import compose_next_step
    from ui.layout_explore import render_explore_panel

    components.inject_theme()
    scope = AnalyticalScope(categories=["Pañales"])
    guidance = GuidanceDecision(
        action="ask_clarification",
        question="¿Querés analizar bebé o adulto?",
        options=["Bebé", "Adulto"],
        chips=[
            GuidanceChip(label="Bebé", action="add_subcategory", args={"subcategory": "Bebé"}),
            GuidanceChip(label="Adulto", action="add_subcategory", args={"subcategory": "Adulto"}),
        ],
    )
    suggested = [
        SuggestedFilter(
            action="filter_category",
            args={"category": "Cabello"},
            label="Ver Cuidado del Cabello — 10 SKUs",
        )
    ]
    slice_data = {
        "dashboard": {
            "skus": 38,
            "understock": 12,
            "stockout_risk": 4,
            "overstock": 1,
            "avg_coverage": 6.4,
            "estimated_purchase_value": 9999,
            "by_category": [],
            "coverage": [],
        },
        "purchase_list": [],
        "evidence": "Por qué ves esto",
        "guidance": guidance.model_dump(),
        "suggested_filters": [s.model_dump() for s in suggested],
    }
    analyze_data = {
        "insight": {"summary": "Resumen", "suggested_questions": ["¿Y el proveedor?"]},
        "insight_source": "fallback",
    }
    step = compose_next_step(
        guidance,
        suggested,
        ["¿Y el proveedor?"],
    )
    render_explore_panel(
        scope=scope,
        slice_data=slice_data,
        analyze_data=analyze_data,
        next_step=step,
        interaction_events=[],
        highlight_calc=None,
        analyst_enabled=True,
        root_skus=441,
    )
    st.caption("harness-ok")


def test_explore_layout_stops_at_charts_without_next_step():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_function(_explore_harness)
    at.run(timeout=15)
    assert not at.exception
    markdown = [str(item.value) for item in at.markdown]

    def _first(needle: str) -> int:
        for i, item in enumerate(markdown):
            if needle in item:
                return i
        return -1

    assert not any("Siguiente paso" in m for m in markdown)
    assert not any("Otros análisis" in m for m in markdown)
    assert not any("Lectura del recorte" in m for m in markdown)
    assert not any("Analista IA" in m for m in markdown)
    assert not any("Refinar recorte" in m for m in markdown)
    assert _first("Qué conviene reponer") >= 0
    assert _first("Cómo está el stock") >= 0
    assert len(at.dataframe) == 0
    buttons = [b.label for b in at.button]
    assert "Bebé" not in buttons
    assert "Adulto" not in buttons


def test_explore_root_scope_hides_inventory_header():
    from streamlit.testing.v1 import AppTest

    def _root_harness() -> None:
        import streamlit as st
        from app.core.models import AnalyticalScope
        from ui import components
        from ui.composition.next_step import compose_next_step
        from ui.layout_explore import render_explore_panel

        components.inject_theme()
        render_explore_panel(
            scope=AnalyticalScope(),
            slice_data={
                "dashboard": {
                    "skus": 13125,
                    "understock": 1322,
                    "stockout_risk": 4022,
                    "avg_coverage": 31.6,
                    "by_category": [
                        {"category": "Pañales", "recommended_quantity": 90, "sku_count": 12}
                    ],
                    "coverage": [{"bucket": "0-7 días", "sku_count": 100}],
                },
                "purchase_list": [],
                "evidence": "",
                "guidance": None,
                "suggested_filters": [],
            },
            analyze_data={},
            next_step=compose_next_step(None, [], []),
            interaction_events=[],
            highlight_calc=None,
            analyst_enabled=False,
            root_skus=13125,
        )

    at = AppTest.from_function(_root_harness)
    at.run(timeout=15)
    assert not at.exception
    markdown = [str(item.value) for item in at.markdown]
    assert not any("Inventario" in m for m in markdown)
    assert not any("13125 → 13125" in m for m in markdown)
    assert not any(b.label == "Limpiar" for b in at.button)


def test_commit_layout_has_no_chart_keys():
    from streamlit.testing.v1 import AppTest

    def _commit_harness() -> None:
        from app.core.models import AnalyticalScope
        from ui import components
        from ui.layout_commit import render_commit_panel

        components.inject_theme()
        render_commit_panel(
            scope=AnalyticalScope(categories=["Pañales"]),
            slice_data={
                "purchase_list": [
                    {
                        "product_id": "1",
                        "product_name": "Pañal",
                        "supplier": "X",
                        "current_stock": 1,
                        "days_of_supply": 1,
                        "recommended_quantity": 10,
                        "operational_priority": "critical",
                        "health_bucket": "stockout_risk",
                    }
                ],
                "evidence": "evidencia",
            },
            analyze_data={
                "commit_summary": {"headline": "OC lista", "oc_summary": "38 líneas"},
                "insight_source": "fallback",
            },
            analyst_enabled=True,
            csv_bytes=b"a,b\n1,2\n",
        )

    at = AppTest.from_function(_commit_harness)
    at.run(timeout=15)
    assert not at.exception
    markdown = [str(item.value) for item in at.markdown]
    assert any("OC propuesta" in m for m in markdown)
    assert not any("Siguiente paso" in m for m in markdown)
    downloads = [d.label for d in at.download_button]
    assert any("Exportar OC" in label for label in downloads)


def test_streamlit_app_renders_single_live_dashboard_for_active_thread(tmp_path, monkeypatch):
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("SUPPLYMATE_THREADS_PATH", str(tmp_path / "threads.json"))
    script = Path(__file__).resolve().parents[3] / "ui" / "streamlit_app.py"
    at = AppTest.from_file(str(script))
    at.session_state["messages"] = [
        {"role": "user", "content": "¿Qué productos tengo que comprar?"},
        {
            "role": "assistant",
            "content": "Primer recorte",
            "mode": "explore",
            "purchase_list": [
                {
                    "product_id": "0",
                    "product_name": "Acondicionador",
                    "supplier": "Prov",
                    "current_stock": 2,
                    "days_of_supply": 5,
                    "recommended_quantity": 8,
                    "operational_priority": "high",
                    "health_bucket": "understock",
                    "average_daily_demand": 1.2,
                }
            ],
            "dashboard": {
                "skus": 500,
                "understock": 20,
                "stockout_risk": 8,
                "avg_coverage": 14.2,
                "by_category": [],
                "coverage": [],
            },
        },
        {
            "role": "assistant",
            "content": "4022 en riesgo de quiebre · 25 para reponer",
            "mode": "explore",
            "purchase_list": [
                {
                    "product_id": "1",
                    "product_name": "Shampoo",
                    "supplier": "Prov",
                    "current_stock": 1,
                    "days_of_supply": 2,
                    "recommended_quantity": 12,
                    "operational_priority": "critical",
                    "health_bucket": "stockout_risk",
                    "average_daily_demand": 2.5,
                }
            ],
            "dashboard": {
                "skus": 2430,
                "understock": 255,
                "stockout_risk": 763,
                "avg_coverage": 30.7,
                "by_category": [
                    {"category": "Cuidado del Cabello", "recommended_quantity": 120, "sku_count": 10}
                ],
                "coverage": [
                    {"bucket": "0-7 días", "sku_count": 40},
                    {"bucket": "8-14 días", "sku_count": 55},
                ],
            },
        },
        {
            "role": "user",
            "content": "que productos tengo que comprar?",
        },
        {
            "role": "assistant",
            "content": "Error 500: Internal Server Error",
            "mode": "error",
        },
    ]
    at.session_state["live_list_active"] = True
    at.session_state["pending_prompt"] = None
    at.session_state["analyst_enabled"] = False
    at.session_state["panel_mode"] = "explore"
    at.session_state["analytical_scope"] = {"categories": ["Cuidado del Cabello"]}
    at.session_state["interaction_events"] = []
    at.session_state["root_question"] = "¿Qué productos tengo que comprar?"
    at.session_state["root_skus"] = 2430
    at.session_state["slice_data"] = {
        "dashboard": {
            "skus": 2430,
            "understock": 255,
            "stockout_risk": 763,
            "avg_coverage": 30.7,
            "by_category": [],
            "coverage": [],
        },
        "purchase_list": [
            {
                "product_id": "1",
                "product_name": "Shampoo",
                "supplier": "Prov",
                "current_stock": 1,
                "days_of_supply": 2,
                "recommended_quantity": 12,
                "operational_priority": "critical",
                "health_bucket": "stockout_risk",
                "average_daily_demand": 2.5,
            }
        ],
        "evidence": "Por qué ves esto",
        "guidance": None,
        "suggested_filters": [],
    }
    at.run(timeout=20)
    assert not at.exception
    markdown = [str(item.value) for item in at.markdown]
    assert not any("Internal Server Error" in m for m in markdown)
    assert not any("Primer recorte" in m for m in markdown)
    assert not any("Cobertura promedio" in m for m in markdown)
    assert any("sm-chat-summary" in m for m in markdown)
    assert not any("Siguiente paso" in m for m in markdown)
    assert not any("Otros análisis" in m for m in markdown)
    assert len(at.dataframe) == 0
    assert any("Qué conviene reponer" in m for m in markdown)
