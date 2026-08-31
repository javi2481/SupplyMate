import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.middleware.rate_limit import reset_rate_limits
from app.models import AnalyticalScope
from app.services import catalog_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean():
    reset_rate_limits()
    from app.services import insight_cache

    insight_cache.reset()
    yield
    reset_rate_limits()
    insight_cache.reset()


def _insight_payload(slice_data):
    n = len(slice_data.purchase_list)
    total = sum(i.recommended_quantity for i in slice_data.purchase_list)
    if n == 0:
        return {
            "panel_title": "Vacío",
            "summary": "0",
            "bullets": [],
            "purchase_priorities": [],
            "navigation_hints": [],
            "suggested_questions": [],
            "highlight_kpis": [],
        }
    item = slice_data.purchase_list[0]
    return {
        "panel_title": "Recorte",
        "summary": f"{n} productos",
        "bullets": [f"{n} SKUs · {total} unidades"],
        "purchase_priorities": [
            {
                "product_id": item.product_id,
                "product_name": item.product_name,
                "recommended_quantity": item.recommended_quantity,
                "reason": "prioridad",
            }
        ],
        "navigation_hints": ["Filtrar cobertura"],
        "suggested_questions": ["¿Qué categoría?"],
        "highlight_kpis": ["stockout_risk"],
    }


def _commit_payload(slice_data):
    insight = _insight_payload(slice_data)
    n = len(slice_data.purchase_list)
    total = sum(i.recommended_quantity for i in slice_data.purchase_list)
    return {
        "headline": "OC lista",
        "oc_summary": f"{n} SKUs · {total} unidades",
        "top_priorities": insight["purchase_priorities"][:1],
        "checklist": ["Revisé cantidades"],
    }


def test_analyze_explore_returns_200():
    scope = AnalyticalScope()
    slice_data = catalog_service.replenishment_slice(scope, limit=25)
    payload = _insight_payload(slice_data)

    async def fake_run(agent, prompt, **kwargs):
        class Result:
            final_output = json.dumps(payload, ensure_ascii=False)

        return Result()

    body = {
        "mode": "explore",
        "scope": scope.model_dump(),
        "events": [],
        "root_question": "¿Qué comprar?",
    }
    with patch("app.agent.Runner.run", new=AsyncMock(side_effect=fake_run)):
        response = client.post("/replenishment/analyze", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["insight_source"] == "llm"
    assert data["insight"]["panel_title"] == "Recorte"


def test_analyze_commit_requires_frozen_scope():
    scope = AnalyticalScope()
    body = {"mode": "commit", "scope": scope.model_dump(), "events": []}
    response = client.post("/replenishment/analyze", json=body)
    assert response.status_code == 422


def test_analyze_commit_with_frozen_scope():
    scope = AnalyticalScope()
    slice_data = catalog_service.replenishment_slice(scope, limit=25)
    commit = _commit_payload(slice_data)

    async def fake_run(agent, prompt, **kwargs):
        class Result:
            final_output = json.dumps(commit, ensure_ascii=False)

        return Result()

    body = {
        "mode": "commit",
        "scope": scope.model_dump(),
        "frozen_scope": scope.model_dump(),
        "events": [],
    }
    with patch("app.agent.Runner.run", new=AsyncMock(side_effect=fake_run)):
        response = client.post("/replenishment/analyze", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["commit_summary"]["headline"] == "OC lista"


def test_analyze_invalid_llm_json_fallback():
    scope = AnalyticalScope()

    async def fake_run(agent, prompt, **kwargs):
        class Result:
            final_output = "not json"

        return Result()

    with patch("app.agent.Runner.run", new=AsyncMock(side_effect=fake_run)):
        response = client.post(
            "/replenishment/analyze",
            json={"mode": "explore", "scope": scope.model_dump(), "events": []},
        )
    assert response.status_code == 200
    assert response.json()["insight_source"] == "fallback"


def test_analyze_rate_limit_429(monkeypatch):
    monkeypatch.setattr(
        "app.middleware.chat_rate_limit.effective_analyze_rate_limit",
        lambda: 1,
    )
    reset_rate_limits()
    scope = AnalyticalScope()
    payload = {"mode": "explore", "scope": scope.model_dump(), "events": []}

    async def fake_run(agent, prompt, **kwargs):
        class Result:
            final_output = json.dumps(_insight_payload(catalog_service.replenishment_slice(limit=3)))

        return Result()

    with patch("app.agent.Runner.run", new=AsyncMock(side_effect=fake_run)):
        assert client.post("/replenishment/analyze", json=payload).status_code == 200
        assert client.post("/replenishment/analyze", json=payload).status_code == 429
