"""Minimal JSON logs for LLM runner calls. No prompt bodies."""

from __future__ import annotations

import json
from typing import Any


def emit(
    *,
    event: str,
    agent: str,
    latency_ms: int,
    intent: str | None = None,
    fallback_used: bool = False,
    insight_source: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "event": event,
        "agent": agent,
        "latency_ms": latency_ms,
        "intent": intent,
        "fallback_used": fallback_used,
        "insight_source": insight_source,
    }
    print(json.dumps(payload, ensure_ascii=False), flush=True)
    return payload
