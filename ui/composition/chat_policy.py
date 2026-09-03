"""Commit chat must not silently drop frozen_scope."""

from __future__ import annotations

from typing import Mapping, Sequence

from ui.composition.chat_titles import is_boilerplate_user_question

_LIVE_MODES = ("list", "explore")


def chat_would_unfreeze(panel_mode: str, response_mode: str) -> bool:
    return panel_mode == "commit" and response_mode in _LIVE_MODES


def is_transport_error_message(content: str | None) -> bool:
    text = (content or "").strip()
    if not text:
        return False
    if text.startswith("Error 500") or text.startswith("Error 503"):
        return True
    return "Internal Server Error" in text


def live_dashboard_index(messages: Sequence[Mapping], *, live: bool) -> int | None:
    if not live:
        return None
    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        if msg.get("role") == "assistant" and msg.get("mode") in _LIVE_MODES:
            return i
    return None


def should_skip_repeat_purchase_query(*, live: bool, prompt: str) -> bool:
    return live and is_boilerplate_user_question(prompt)


def hide_history_message(
    messages: Sequence[Mapping],
    index: int,
    *,
    live: bool = False,
) -> bool:
    msg = messages[index]
    if msg.get("role") == "assistant" and is_transport_error_message(msg.get("content")):
        return True
    live_idx = live_dashboard_index(messages, live=live)
    if (
        live
        and live_idx is not None
        and msg.get("role") == "assistant"
        and msg.get("mode") in _LIVE_MODES
        and index != live_idx
    ):
        return True
    if msg.get("role") != "user":
        return False
    text = str(msg.get("content") or "")
    if not is_boilerplate_user_question(text):
        return False
    return any(
        earlier.get("role") == "user"
        and is_boilerplate_user_question(str(earlier.get("content") or ""))
        for earlier in messages[:index]
    )
