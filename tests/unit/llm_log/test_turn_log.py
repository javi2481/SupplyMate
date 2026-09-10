import json

from app.agent.turn_log import (
    build_turn_trace,
    chart_hint_from_scope,
    emit_turn,
    read_recent_turns,
    scope_summary,
)
from app.core.models import (
    AnalyticalScope,
    ChatResponse,
    InventoryDashboard,
    QueryInterpretation,
    Reference,
    ResolvedReference,
)


def test_chart_hint_list_shaped():
    assert (
        chart_hint_from_scope(
            AnalyticalScope(categories=["Cosmetica"], health_buckets=["stockout_risk"])
        )
        == "sku"
    )
    assert chart_hint_from_scope(AnalyticalScope(categories=["Cosmetica"])) == "subcategory"
    assert chart_hint_from_scope(AnalyticalScope()) == "category"


def test_build_turn_trace_includes_route_scope_answer(capsys, tmp_path, monkeypatch):
    monkeypatch.setenv("SUPPLYMATE_TURN_LOG", str(tmp_path / "turns.jsonl"))
    monkeypatch.setenv("SUPPLYMATE_ENV", "development")
    scope = AnalyticalScope(
        categories=["Cosmetica"],
        health_buckets=["stockout_risk"],
        coverage_buckets=["0–3 días"],
        horizon_days=60,
    )
    response = ChatResponse(
        answer="Cosmetica · críticos · 79904 unidades.",
        mode="explore",
        scope=scope,
        dashboard=InventoryDashboard(
            skus=182,
            purchase_skus=182,
            recommended_units=79904,
            by_category=[],
            by_subcategory=[],
        ),
        purchase_list=[],
    )
    interp = QueryInterpretation(
        intent="inventory_risk",
        references=[Reference(text="cosmética", kind="product_group")],
        filter_hints=["criticos", "0–3 días"],
        source="llm",
        relation="new_query",
    )
    resolved = [
        ResolvedReference(
            user_text="cosmética",
            match_kind="group",
            scope_dimension="category",
            scope_value="Cosmetica",
            label="Cosmetica",
        )
    ]
    trace = build_turn_trace(
        message="mostrame críticos de cosmética con menos de 3 días",
        previous=AnalyticalScope(categories=["Cosmetica"]),
        interpretation=interp,
        resolved=resolved,
        response=response,
        route="explore",
        latency_ms=42,
    )
    emit_turn(trace)
    out = capsys.readouterr().out.strip()
    data = json.loads(out)
    assert data["event"] == "chat.turn"
    assert data["route"] == "explore"
    assert data["chart_hint"] == "sku"
    assert data["scope"]["categories"] == ["Cosmetica"]
    assert data["dashboard"]["recommended_units"] == 79904
    assert "críticos" in data["answer_preview"]
    assert "prompt" not in data
    recent = read_recent_turns(5)
    assert recent
    assert recent[-1]["turn_id"] == data["turn_id"]


def test_scope_summary_empty():
    assert scope_summary(None) == {}
