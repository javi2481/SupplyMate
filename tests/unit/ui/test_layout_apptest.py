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


def test_explore_layout_has_single_next_step_heading():
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

    next_headings = [m for m in markdown if "Siguiente paso" in m]
    assert len(next_headings) == 1
    assert _first("Siguiente paso") < _first("Cantidad recomendada")
    assert _first("Cantidad recomendada") < _first("Lectura del recorte")
    assert any("Lectura del recorte" in m for m in markdown)
    assert not any("Analista IA" in m for m in markdown)
    assert not any("Refinar recorte" in m for m in markdown)
    buttons = [b.label for b in at.button]
    assert "Bebé" in buttons
    assert "Adulto" in buttons
    others = [b for b in buttons if "Cabello" in b or "proveedor" in b.lower()]
    assert others


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
