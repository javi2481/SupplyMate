import csv
import io
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.api import app
from app.middleware.rate_limit import reset_rate_limits
from app.models import AnalyticalScope, ChatResponse

client = TestClient(app)

_SLICE_KEYS = {"scope", "evidence", "dashboard", "purchase_list", "suggested_filters", "guidance"}
_DASHBOARD_KEYS = {
    "skus",
    "stockout_risk",
    "understock",
    "overstock",
    "healthy",
    "by_category",
}
_ANALYZE_KEYS = {
    "mode",
    "scope",
    "evidence",
    "dashboard",
    "purchase_list",
    "insight_source",
}
_CSV_HEADERS = [
    "barcode",
    "product_id",
    "product_name",
    "supplier",
    "recommended_quantity",
    "operational_priority",
    "estimated_purchase_value",
]


def _minimal_chat_explore() -> ChatResponse:
    scope = AnalyticalScope(categories=["Pañales"])
    return ChatResponse(
        answer="ok",
        mode="explore",
        scope=scope,
        dashboard=None,
    )


def test_contract_replenishment_slice_schema():
    response = client.get("/replenishment/slice", params={"limit": 3})
    assert response.status_code == 200
    data = response.json()
    assert _SLICE_KEYS.issubset(data.keys())
    dashboard = data["dashboard"]
    assert _DASHBOARD_KEYS.issubset(dashboard.keys())
    assert isinstance(dashboard["skus"], int)
    assert isinstance(dashboard["by_category"], list)
    assert isinstance(data["purchase_list"], list)


def test_contract_purchase_list_csv_headers():
    response = client.get("/replenishment/purchase-list.csv", params={"limit": 3})
    assert response.status_code == 200
    rows = list(csv.reader(io.StringIO(response.text)))
    assert rows[0] == _CSV_HEADERS


def test_contract_analyze_response_schema():
    scope = AnalyticalScope()
    payload = {"mode": "explore", "scope": scope.model_dump(), "events": []}

    async def fake_run(agent, prompt, **kwargs):
        class Result:
            final_output = "not json"

        return Result()

    with patch("app.agent.Runner.run", new=AsyncMock(side_effect=fake_run)):
        response = client.post("/replenishment/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert _ANALYZE_KEYS.issubset(data.keys())
    assert data["insight_source"] in {"llm", "fallback"}


def test_contract_chat_response_schema():
    reset_rate_limits()
    with patch(
        "app.api.run_supplymate",
        new=AsyncMock(return_value=_minimal_chat_explore()),
    ):
        response = client.post("/chat", json={"message": "hola"})
    assert response.status_code == 200
    data = response.json()
    assert {"answer", "mode"}.issubset(data.keys())
    assert data["mode"] == "explore"
    assert data["scope"] is not None
    assert isinstance(data["scope"], dict)
