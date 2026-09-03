"""Title helpers for chat threads — skip boilerplate startup questions."""

from __future__ import annotations

import unicodedata

from ui.composition import copy as ui_copy


def normalize_question(text: str) -> str:
    cleaned = text.strip().lower()
    if cleaned.startswith("¿"):
        cleaned = cleaned[1:]
    cleaned = cleaned.rstrip("?").strip()
    cleaned = " ".join(cleaned.split())
    decomposed = unicodedata.normalize("NFKD", cleaned)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def is_boilerplate_user_question(text: str) -> bool:
    norm = normalize_question(text)
    if not norm:
        return False
    return norm in {normalize_question(q) for q in ui_copy.BOILERPLATE_USER_QUESTIONS}
