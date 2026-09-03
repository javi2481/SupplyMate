"""LLM agents, tools, intent routing, and orchestration entrypoints."""

from __future__ import annotations

from typing import Any

__all__ = [
    "build_commit_agent",
    "build_explain_agent",
    "build_insight_agent",
    "build_supply_agent",
    "get_model",
    "run_analyze",
    "run_apply_chip",
    "run_supplymate",
]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from app.agent import runner

        return getattr(runner, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
