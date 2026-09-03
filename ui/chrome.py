"""Minimal chrome: header, home, next-step block."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from ui.composition import copy as ui_copy
from ui.composition.next_step import NextStep, NextStepOption
from ui.threads.rail import render_thread_rail


def render_header(panel_mode: str, *, live: bool) -> None:
    mode_label = ui_copy.MODE_COMMIT if panel_mode == "commit" else ui_copy.MODE_EXPLORE
    if not live:
        mode_label = ui_copy.MODE_EXPLORE
    st.markdown(f"## {ui_copy.APP_NAME}")
    st.caption(f"{ui_copy.APP_TAGLINE} · {mode_label}")


def render_home(*, on_example: Callable[[str], None] | None = None) -> None:
    st.markdown(ui_copy.HOME_HINT)
    examples = [
        "¿Qué productos tengo que comprar?",
        "¿Cuántos pañales tengo que pedir?",
    ]
    for i, example in enumerate(examples):
        if st.button(example, key=f"home-ex-{i}"):
            if on_example:
                on_example(example)
            else:
                st.session_state.pending_prompt = example
            st.rerun()


def render_next_step(
    step: NextStep,
    *,
    key_prefix: str,
    on_option: Callable[[NextStepOption], None] | None = None,
    on_prompt: Callable[[str], None] | None = None,
    show_title: bool = True,
) -> None:
    if not step.primary and not step.secondary and not step.prompts and not step.question:
        return
    if show_title:
        st.markdown(f"### {ui_copy.NEXT_STEP_TITLE}")
    if step.progress_label:
        st.caption(
            f"Paso {step.progress_step} de {step.progress_total} · {step.progress_label}"
        )
    if step.question:
        st.markdown(step.question)
    for i, opt in enumerate(step.primary):
        if st.button(opt.label, key=f"{key_prefix}-p-{i}", type="primary"):
            if on_option:
                on_option(opt)
            elif opt.kind == "prompt" and on_prompt:
                on_prompt(opt.label)
            st.rerun()
        if opt.caption:
            st.caption(opt.caption)
    extras = list(step.secondary)
    if step.prompts:
        extras.extend(
            NextStepOption(kind="prompt", label=prompt) for prompt in step.prompts
        )
    if extras:
        st.caption(ui_copy.OTHER_ANALYSES)
        for i, opt in enumerate(extras):
            if st.button(opt.label, key=f"{key_prefix}-s-{i}"):
                if opt.kind == "prompt":
                    if on_prompt:
                        on_prompt(opt.label)
                    else:
                        st.session_state.pending_prompt = opt.label
                elif on_option:
                    on_option(opt)
                st.rerun()
