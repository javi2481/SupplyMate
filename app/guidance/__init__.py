"""Guided selling: chips, missions, facets, next-question engine."""

from __future__ import annotations

from typing import Any

__all__ = [
    "guidance_after_slice",
    "guidance_for_resolution",
    "pick_next_question",
    "preview_union",
]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from app.guidance import engine

        return getattr(engine, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
