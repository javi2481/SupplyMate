"""Siguiente paso: present guidance, suggested filters, and LLM prompts as one block."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.models import GuidanceDecision, SuggestedFilter
from app.services.analytics import metrics
from app.services.scoping import suggested_filters as sf
from ui.composition import copy as ui_copy

_GUIDANCE_PRIMARY_ACTIONS = {"ask_clarification", "draft_oc"}


@dataclass(frozen=True)
class NextStepOption:
    kind: str
    label: str
    guidance_chip: dict[str, Any] | None = None
    filter_action: str | None = None
    filter_args: dict[str, str] | None = None
    caption: str = ""


@dataclass(frozen=True)
class NextStep:
    question: str
    primary: list[NextStepOption]
    secondary: list[NextStepOption] = field(default_factory=list)
    prompts: list[str] = field(default_factory=list)
    progress_label: str = ""
    progress_step: int = 0
    progress_total: int = 0


def _as_guidance(raw: GuidanceDecision | dict | None) -> GuidanceDecision | None:
    if raw is None:
        return None
    if isinstance(raw, GuidanceDecision):
        return raw
    return GuidanceDecision.model_validate(raw)


def _as_filters(raw: list[SuggestedFilter] | list[dict] | None) -> list[SuggestedFilter]:
    items: list[SuggestedFilter] = []
    for item in raw or []:
        if isinstance(item, SuggestedFilter):
            items.append(item)
        else:
            items.append(SuggestedFilter.model_validate(item))
    return items


def _norm(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def _guidance_health_buckets(guidance: GuidanceDecision) -> set[str]:
    buckets: set[str] = set()
    for chip in guidance.chips:
        if chip.action == "add_health_bucket":
            bucket = (chip.args or {}).get("health_bucket")
            if bucket:
                buckets.add(bucket)
    return buckets


def _guidance_option_labels(guidance: GuidanceDecision) -> set[str]:
    labels = {_norm(opt) for opt in guidance.options if opt}
    for chip in guidance.chips:
        if chip.label:
            labels.add(_norm(chip.label))
    return labels


def _display_chip_label(chip) -> str:
    if chip.action == "draft_oc":
        return ui_copy.REVIEW_PURCHASE
    return chip.label


def _filter_duplicates_guidance(
    filt: SuggestedFilter,
    *,
    health_buckets: set[str],
    option_labels: set[str],
) -> bool:
    if filt.action == sf.ACTION_FILTER_HEALTH:
        bucket = (filt.args or {}).get("health_bucket")
        if bucket and bucket in health_buckets:
            return True
        if bucket == metrics.BUCKET_STOCKOUT_RISK and any(
            "quiebre" in label for label in option_labels
        ):
            return True
    if filt.label and _norm(filt.label) in option_labels:
        return True
    return False


def compose_next_step(
    guidance: GuidanceDecision | dict | None,
    suggested_filters: list[SuggestedFilter] | list[dict] | None,
    suggested_questions: list[str] | None = None,
) -> NextStep:
    decision = _as_guidance(guidance)
    filters = _as_filters(suggested_filters)
    prompts = [q for q in (suggested_questions or []) if (q or "").strip()][:3]

    primary: list[NextStepOption] = []
    question = ""
    progress_label = ""
    progress_step = 0
    progress_total = 0
    health_buckets: set[str] = set()
    option_labels: set[str] = set()

    if decision and decision.action in _GUIDANCE_PRIMARY_ACTIONS and (
        decision.question or decision.chips or decision.options
    ):
        question = decision.question or ui_copy.NEXT_STEP_FALLBACK
        progress_label = decision.progress_label
        progress_step = decision.progress_step
        progress_total = decision.progress_total
        health_buckets = _guidance_health_buckets(decision)
        option_labels = _guidance_option_labels(decision)
        chips = list(decision.chips)
        if chips:
            for chip in chips[:6]:
                primary.append(
                    NextStepOption(
                        kind="guidance",
                        label=_display_chip_label(chip),
                        guidance_chip=chip.model_dump(),
                        caption=chip.caption,
                    )
                )
        else:
            for opt in decision.options[:6]:
                primary.append(NextStepOption(kind="prompt", label=opt))

    secondary: list[NextStepOption] = []
    for filt in filters:
        if _filter_duplicates_guidance(
            filt, health_buckets=health_buckets, option_labels=option_labels
        ):
            continue
        secondary.append(
            NextStepOption(
                kind="filter",
                label=filt.label,
                filter_action=filt.action,
                filter_args=dict(filt.args or {}),
            )
        )
        if len(secondary) >= 3:
            break

    if not primary and secondary:
        promoted = secondary[0]
        primary = [promoted]
        secondary = secondary[1:]
        question = question or ui_copy.NEXT_STEP_FALLBACK

    return NextStep(
        question=question,
        primary=primary,
        secondary=secondary,
        prompts=prompts,
        progress_label=progress_label,
        progress_step=progress_step,
        progress_total=progress_total,
    )


def _option_covered_by_charts(
    opt: NextStepOption,
    *,
    has_category_chart: bool,
    has_coverage_chart: bool,
) -> bool:
    if opt.kind == "filter":
        if opt.filter_action == sf.ACTION_FILTER_CATEGORY and has_category_chart:
            return True
        if opt.filter_action == sf.ACTION_FILTER_COVERAGE and has_coverage_chart:
            return True
    action = (opt.guidance_chip or {}).get("action")
    if action == "add_category" and has_category_chart:
        return True
    if action == "add_coverage_bucket" and has_coverage_chart:
        return True
    return False


def _is_draft_oc(opt: NextStepOption) -> bool:
    return (opt.guidance_chip or {}).get("action") == "draft_oc"


def split_next_step_around_charts(
    step: NextStep,
    *,
    has_category_chart: bool,
    has_coverage_chart: bool,
) -> tuple[NextStep, NextStep]:
    """Clarification before charts; leftover chips after. Category/coverage chips drop when charts exist."""

    def covered(opt: NextStepOption) -> bool:
        return _option_covered_by_charts(
            opt,
            has_category_chart=has_category_chart,
            has_coverage_chart=has_coverage_chart,
        )

    before_primary = [opt for opt in step.primary if not covered(opt) and not _is_draft_oc(opt)]
    after_primary = [opt for opt in step.primary if _is_draft_oc(opt)]
    after_secondary = [opt for opt in step.secondary if not covered(opt)]
    question = step.question
    if question == ui_copy.NEXT_STEP_FALLBACK and not before_primary:
        question = ""
    before = NextStep(
        question=question,
        primary=before_primary,
        progress_label=step.progress_label,
        progress_step=step.progress_step,
        progress_total=step.progress_total,
    )
    after = NextStep(
        question="",
        primary=after_primary,
        secondary=after_secondary,
        prompts=step.prompts,
    )
    return before, after
