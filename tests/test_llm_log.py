import json

from app.llm_log import emit


def test_emit_prints_json_without_prompt(capsys):
    payload = emit(
        event="runner.run",
        agent="SupplyMateIntent",
        latency_ms=12,
        intent="purchase_list",
        fallback_used=False,
        insight_source=None,
    )
    captured = capsys.readouterr().out.strip()
    data = json.loads(captured)
    assert data["event"] == "runner.run"
    assert data["agent"] == "SupplyMateIntent"
    assert data["latency_ms"] == 12
    assert data["intent"] == "purchase_list"
    assert "prompt" not in data
    assert payload == data
