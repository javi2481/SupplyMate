"""Session-only AnalyticalScope history (UI navigation, not API)."""

from __future__ import annotations

from typing import Any

from app.core.models import AnalyticalScope

HISTORY_CAP = 20


def clear() -> list[AnalyticalScope]:
    return []


def push(history: list[AnalyticalScope], scope: AnalyticalScope) -> list[AnalyticalScope]:
    dump = scope.model_dump()
    if history and history[-1].model_dump() == dump:
        return list(history)
    out = list(history) + [AnalyticalScope.model_validate(dump)]
    if len(out) > HISTORY_CAP:
        out = out[-HISTORY_CAP:]
    return out


def pop(
    history: list[AnalyticalScope],
) -> tuple[AnalyticalScope, list[AnalyticalScope]] | None:
    if not history:
        return None
    restored = history[-1]
    return restored, list(history[:-1])


def loads(raw: Any) -> list[AnalyticalScope]:
    if not raw:
        return []
    if not isinstance(raw, list):
        return []
    out: list[AnalyticalScope] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            out.append(AnalyticalScope.model_validate(item))
        except Exception:
            continue
    if len(out) > HISTORY_CAP:
        out = out[-HISTORY_CAP:]
    return out
