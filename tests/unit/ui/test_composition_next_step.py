"""Tests for compose_next_step (no Streamlit, no HTTP)."""

from __future__ import annotations

from app.core.models import GuidanceChip, GuidanceDecision, SuggestedFilter
from app.services.analytics import metrics
from app.services.scoping import suggested_filters
from ui.composition.next_step import compose_next_step


def _guidance_baby_adult() -> GuidanceDecision:
    return GuidanceDecision(
        action="ask_clarification",
        question="¿Querés analizar bebé o adulto?",
        options=["Bebé", "Adulto"],
        chips=[
            GuidanceChip(label="Bebé", action="add_subcategory", args={"subcategory": "Bebé"}),
            GuidanceChip(label="Adulto", action="add_subcategory", args={"subcategory": "Adulto"}),
        ],
        progress_label="Categoría",
        progress_step=1,
        progress_total=4,
    )


def _category_filter() -> SuggestedFilter:
    return SuggestedFilter(
        action=suggested_filters.ACTION_FILTER_CATEGORY,
        args={"category": "Cabello"},
        label="Ver Cuidado del Cabello — 10 SKUs",
    )


def _stockout_filter() -> SuggestedFilter:
    return SuggestedFilter(
        action=suggested_filters.ACTION_FILTER_HEALTH,
        args={"health_bucket": metrics.BUCKET_STOCKOUT_RISK},
        label="Ver riesgo de quiebre — 5 SKUs",
    )


def test_guidance_is_primary_filters_are_secondary():
    step = compose_next_step(
        _guidance_baby_adult(),
        [_category_filter()],
        ["¿Qué pasa con cobertura?"],
    )
    assert step.question == "¿Querés analizar bebé o adulto?"
    assert [opt.label for opt in step.primary] == ["Bebé", "Adulto"]
    assert all(opt.kind == "guidance" for opt in step.primary)
    assert [opt.label for opt in step.secondary] == ["Ver Cuidado del Cabello — 10 SKUs"]
    assert step.prompts == ["¿Qué pasa con cobertura?"]


def test_stockout_not_duplicated_when_guidance_offers_it():
    guidance = GuidanceDecision(
        action="ask_clarification",
        question="¿Filtramos quiebre?",
        options=["Solo riesgo de quiebre"],
        chips=[
            GuidanceChip(
                label="Solo riesgo de quiebre",
                action="add_health_bucket",
                args={"health_bucket": metrics.BUCKET_STOCKOUT_RISK},
            )
        ],
    )
    step = compose_next_step(guidance, [_stockout_filter(), _category_filter()], [])
    assert not any(
        opt.kind == "filter"
        and opt.filter_action == suggested_filters.ACTION_FILTER_HEALTH
        for opt in step.secondary
    )
    assert any("Cabello" in opt.label for opt in step.secondary)


def test_llm_questions_never_primary():
    step = compose_next_step(None, [], ["Pregunta A", "Pregunta B"])
    assert step.primary == []
    assert step.prompts == ["Pregunta A", "Pregunta B"]


def test_without_guidance_first_filter_becomes_primary():
    step = compose_next_step(None, [_category_filter(), _stockout_filter()], [])
    assert len(step.primary) == 1
    assert step.primary[0].kind == "filter"
    assert "Cabello" in step.primary[0].label
    assert len(step.secondary) == 1
    assert step.secondary[0].filter_action == suggested_filters.ACTION_FILTER_HEALTH


def test_draft_oc_primary_uses_review_label():
    guidance = GuidanceDecision(
        action="draft_oc",
        question="¿Armamos la OC de este recorte?",
        options=["Armar OC de este recorte"],
        chips=[
            GuidanceChip(label="Armar OC de este recorte", action="draft_oc", args={}),
        ],
    )
    step = compose_next_step(guidance, [_category_filter()], [])
    assert step.primary[0].kind == "guidance"
    assert step.primary[0].label == "Revisar compra"
    assert step.primary[0].guidance_chip["action"] == "draft_oc"
    assert step.secondary


def test_chart_covered_filters_move_out_of_next_step_chips():
    from ui.composition.next_step import split_next_step_around_charts

    step = compose_next_step(None, [_category_filter(), _stockout_filter()], ["¿Y el proveedor?"])
    before, after = split_next_step_around_charts(
        step, has_category_chart=True, has_coverage_chart=True
    )
    assert before.primary == []
    assert before.question == ""
    assert all(opt.filter_action != suggested_filters.ACTION_FILTER_CATEGORY for opt in after.secondary)
    assert any(opt.filter_action == suggested_filters.ACTION_FILTER_HEALTH for opt in after.secondary)
    assert after.prompts == ["¿Y el proveedor?"]


def test_clarification_stays_before_charts():
    from ui.composition.next_step import split_next_step_around_charts

    step = compose_next_step(_guidance_baby_adult(), [_category_filter()], [])
    before, after = split_next_step_around_charts(
        step, has_category_chart=True, has_coverage_chart=False
    )
    assert before.question == "¿Querés analizar bebé o adulto?"
    assert [opt.label for opt in before.primary] == ["Bebé", "Adulto"]
    assert not any("Cabello" in opt.label for opt in before.primary)
    assert not any("Cabello" in opt.label for opt in after.secondary)
