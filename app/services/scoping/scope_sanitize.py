"""Sanitize analytical scope query values."""

from __future__ import annotations

from app.core.config import MAX_SCOPE_VALUE_LENGTH


def sanitize_value(value: str) -> str | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    if len(cleaned) > MAX_SCOPE_VALUE_LENGTH:
        return None
    return cleaned


def sanitize_values(values: list[str] | None) -> list[str]:
    if not values:
        return []
    out: list[str] = []
    for raw in values:
        cleaned = sanitize_value(raw)
        if cleaned is not None:
            out.append(cleaned)
    return out
