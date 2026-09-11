import csv
import io
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.api import app
from app.core.models import AnalyticalScope, ChatResponse
from app.middleware.rate_limit import reset_rate_limits

client = TestClient(app)

_SLICE_KEYS = {"scope", "evidence", "dashboard", "purchase_list", "suggested_filters", "guidance"}
_DASHBOARD_KEYS = {
    "skus",
    "stockout_risk",
    "understock",
    "overstock",
    "healthy",
    "by_category",
    "recommended_units",
    "purchase_skus",
    "out_of_stock",
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
    assert isinstance(dashboard["recommended_units"], int)
    assert isinstance(dashboard["purchase_skus"], int)
    assert isinstance(dashboard["out_of_stock"], int)


def test_contract_dashboard_totals_cover_full_recorte_not_list():
    data = client.get("/replenishment/slice", params={"limit": 50}).json()
    dashboard = data["dashboard"]
    listed_qty = sum(int(item["recommended_quantity"] or 0) for item in data["purchase_list"])
    listed_n = len(data["purchase_list"])
    assert dashboard["recommended_units"] >= listed_qty
    assert dashboard["purchase_skus"] >= listed_n
    assert dashboard["recommended_units"] > listed_qty or dashboard["purchase_skus"] > listed_n


def test_contract_slice_out_of_stock_filters_zero_stock():
    response = client.get(
        "/replenishment/slice",
        params=[("out_of_stock", "true"), ("limit", "50")],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["dashboard"]["out_of_stock"] == data["dashboard"]["skus"]
    for item in data["purchase_list"]:
        assert item["current_stock"] == 0


def test_contract_slice_coverage_bucket_filters():
    """coverage_bucket must use COVERAGE_ORDER labels (en-dash), e.g. '0–3 días'."""
    response = client.get(
        "/replenishment/slice",
        params=[("coverage_bucket", "0–3 días"), ("limit", "50")],
    )
    assert response.status_code == 200
    data = response.json()
    assert "purchase_list" in data
    assert len(data["purchase_list"]) > 0
    for item in data["purchase_list"]:
        dos = item.get("days_of_supply")
        assert dos is not None
        assert dos < 3


def test_contract_slice_coverage_bucket_14_to_30():
    response = client.get(
        "/replenishment/slice",
        params=[("coverage_bucket", "14–30 días"), ("limit", "50")],
    )
    assert response.status_code == 200
    items = response.json()["purchase_list"]
    assert len(items) > 0
    for item in items:
        dos = item.get("days_of_supply")
        assert dos is not None
        assert 14 <= dos < 30


def test_contract_slice_coverage_bucket_30_plus():
    response = client.get(
        "/replenishment/slice",
        params=[("coverage_bucket", "30+ días"), ("limit", "50")],
    )
    assert response.status_code == 200
    items = response.json()["purchase_list"]
    assert len(items) > 0
    for item in items:
        dos = item.get("days_of_supply")
        assert dos is not None
        assert dos >= 30


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

    with patch("app.agent.runner.Runner.run", new=AsyncMock(side_effect=fake_run)):
        response = client.post("/replenishment/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert _ANALYZE_KEYS.issubset(data.keys())
    assert data["insight_source"] in {"llm", "fallback"}


def test_contract_slice_filters_coverage_bucket():
    unfiltered = client.get("/replenishment/slice", params={"limit": 100}).json()["purchase_list"]
    filtered = client.get(
        "/replenishment/slice",
        params={"coverage_bucket": "0–3 días", "limit": 100},
    ).json()["purchase_list"]

    assert all(
        item["days_of_supply"] is not None and item["days_of_supply"] < 3 for item in filtered
    )
    outside_ids = {
        item["product_id"]
        for item in unfiltered
        if item["days_of_supply"] is not None and item["days_of_supply"] >= 3
    }
    if outside_ids:
        assert outside_ids.isdisjoint({item["product_id"] for item in filtered})


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
