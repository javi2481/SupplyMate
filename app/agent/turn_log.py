"""Structured chat-turn traces for debugging recorte / routing / answers.

General observability — not tied to any one NL question. Emits JSON to stdout
and appends JSONL under logs/chat-turns.jsonl (override with SUPPLYMATE_TURN_LOG).
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import REPO_ROOT, is_production
from app.core.models import (
    AnalyticalScope,
    ChatResponse,
    InventoryDashboard,
    QueryInterpretation,
    ResolvedReference,
)

_DEFAULT_LOG = REPO_ROOT / "logs" / "chat-turns.jsonl"
_ANSWER_PREVIEW = 280
_MESSAGE_PREVIEW = 240


def turn_log_path() -> Path:
    raw = (os.getenv("SUPPLYMATE_TURN_LOG") or "").strip()
    return Path(raw) if raw else _DEFAULT_LOG


def scope_summary(scope: AnalyticalScope | None) -> dict[str, Any]:
    if scope is None:
        return {}
    return {
        "categories": list(scope.categories),
        "subcategories": list(scope.subcategories),
        "health_buckets": list(scope.health_buckets),
        "coverage_buckets": list(scope.coverage_buckets),
        "suppliers": list(scope.suppliers),
        "name_tokens": list(scope.name_tokens),
        "out_of_stock_only": bool(scope.out_of_stock_only),
        "horizon_days": scope.horizon_days,
        "highlight_product_id": scope.highlight_product_id or "",
    }


def dashboard_summary(dash: InventoryDashboard | None) -> dict[str, Any]:
    if dash is None:
        return {}
    return {
        "skus": dash.skus,
        "purchase_skus": dash.purchase_skus,
        "recommended_units": dash.recommended_units,
        "stockout_risk": dash.stockout_risk,
        "out_of_stock": dash.out_of_stock,
        "by_category": [
            {"name": b.category, "units": b.recommended_quantity} for b in dash.by_category[:8]
        ],
        "by_subcategory": [
            {"name": b.category, "units": b.recommended_quantity}
            for b in (dash.by_subcategory or [])[:8]
        ],
    }


def chart_hint_from_scope(scope: AnalyticalScope | None) -> str:
    """Server-side mirror of Explore chart policy (list-shaped → top SKUs)."""
    if scope is None:
        return "category"
    list_shaped = bool(
        scope.health_buckets
        or scope.coverage_buckets
        or scope.suppliers
        or scope.name_tokens
        or scope.out_of_stock_only
    )
    if list_shaped:
        return "sku"
    if len(scope.categories) == 1 and not scope.subcategories:
        return "subcategory"
    if scope.subcategories:
        return "subcategory"
    return "category"


def resolved_summary(resolved: list[ResolvedReference]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for ref in resolved:
        out.append(
            {
                "text": ref.user_text,
                "match_kind": ref.match_kind,
                "scope_dimension": ref.scope_dimension,
                "scope_value": ref.scope_value,
                "product_id": ref.product_id or "",
                "label": ref.label or "",
            }
        )
    return out


def build_turn_trace(
    *,
    message: str,
    previous: AnalyticalScope | None,
    interpretation: QueryInterpretation | None,
    resolved: list[ResolvedReference],
    response: ChatResponse | None,
    route: str,
    latency_ms: int,
    error: str | None = None,
) -> dict[str, Any]:
    answer = (response.answer if response else "") or ""
    scope = response.scope if response else None
    dash = response.dashboard if response else None
    return {
        "event": "chat.turn",
        "turn_id": str(uuid.uuid4()),
        "ts": datetime.now(timezone.utc).isoformat(),
        "route": route,
        "latency_ms": latency_ms,
        "message": (message or "")[:_MESSAGE_PREVIEW],
        "previous_scope": scope_summary(previous),
        "interpretation": {
            "intent": interpretation.intent if interpretation else None,
            "relation": interpretation.relation if interpretation else None,
            "source": interpretation.source if interpretation else None,
            "confidence": interpretation.confidence if interpretation else None,
            "filter_hints": list(interpretation.filter_hints) if interpretation else [],
            "references": [
                {"text": r.text, "kind": r.kind}
                for r in (interpretation.references if interpretation else [])
            ],
        },
        "resolved": resolved_summary(resolved),
        "scope": scope_summary(scope),
        "chart_hint": chart_hint_from_scope(scope),
        "dashboard": dashboard_summary(dash),
        "mode": response.mode if response else None,
        "product_id": (response.product_id if response else "") or "",
        "purchase_list_n": len(response.purchase_list) if response else 0,
        "answer_preview": answer[:_ANSWER_PREVIEW],
        "error": error,
    }


def emit_turn(trace: dict[str, Any]) -> dict[str, Any]:
    """Print one JSON line; append JSONL outside test env (or when SUPPLYMATE_TURN_LOG is set)."""
    from app.core.config import is_test_env

    line = json.dumps(trace, ensure_ascii=False)
    print(line, flush=True)
    explicit = (os.getenv("SUPPLYMATE_TURN_LOG") or "").strip()
    if is_test_env() and not explicit:
        return trace
    if is_production() and not explicit:
        return trace
    disabled = os.getenv("SUPPLYMATE_TURN_LOG_FILE", "1").strip().lower() in {
        "0",
        "false",
        "no",
        "off",
    }
    if disabled:
        return trace
    path = turn_log_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass
    return trace


def attach_trace(response: ChatResponse, trace: dict[str, Any]) -> ChatResponse:
    return response.model_copy(update={"trace": trace})


def read_recent_turns(limit: int = 20) -> list[dict[str, Any]]:
    path = turn_log_path()
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out: list[dict[str, Any]] = []
    for line in lines[-max(1, limit) :]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out
