from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.api import app
from app.models import ChatResponse, ProductContext, ProductNotFoundError, ReplenishmentResult
from app.services import catalog_service
from tests.catalog_ids import SKU_HIGH_QTY, SKU_UNKNOWN, SKU_ZERO_QTY

client = TestClient(app)


def _sample_chat_response() -> ChatResponse:
    rec = catalog_service.get_replenishment_recommendation(SKU_HIGH_QTY)
    return ChatResponse(
        answer=f"Recomiendo pedir {rec.recommended_quantity} unidades.",
        mode="single",
        product_id=rec.product_id,
        product_name=rec.product_name,
        recommended_quantity=rec.recommended_quantity,
        calculation=rec.calculation,
        context=rec.context,
    )


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_search_products():
    response = client.get("/products/search", params={"q": "47 street"})
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert body
    assert any(h["product_id"] == SKU_ZERO_QTY for h in body)


def test_get_product():
    response = client.get(f"/products/{SKU_ZERO_QTY}")
    assert response.status_code == 200
    body = response.json()
    assert body["product_id"] == SKU_ZERO_QTY
    assert body["current_stock"] >= 0


def test_get_product_not_found():
    response = client.get(f"/products/{SKU_UNKNOWN}")
    assert response.status_code == 404


def test_get_replenishment():
    response = client.get(f"/products/{SKU_HIGH_QTY}/replenishment")
    assert response.status_code == 200
    body = response.json()
    assert body["recommended_quantity"] == 173
    assert body["product_id"] == SKU_HIGH_QTY


def test_chat_success():
    mocked = _sample_chat_response()
    with patch("app.api.run_supplymate", new=AsyncMock(return_value=mocked)):
        response = client.post(
            "/chat",
            json={"message": f"¿Cuánto debería pedir de {SKU_HIGH_QTY}?"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["product_id"] == SKU_HIGH_QTY
    assert body["recommended_quantity"] == 173
    assert "answer" in body


def test_chat_not_found():
    with patch(
        "app.api.run_supplymate",
        new=AsyncMock(side_effect=ProductNotFoundError(SKU_UNKNOWN)),
    ):
        response = client.post(
            "/chat",
            json={"message": f"¿Cuánto pedir de {SKU_UNKNOWN}?"},
        )
    assert response.status_code == 404


def test_purchase_list_endpoint():
    response = client.get("/replenishment/purchase-list", params={"limit": 5})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 5
    assert all(item["recommended_quantity"] > 0 for item in body)
    assert all("product_name" in item for item in body)
    assert all("product_id" in item and item["product_id"] for item in body)
    assert all("health_bucket" in item for item in body)


def test_dashboard_endpoint():
    response = client.get("/replenishment/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert body["skus"] > 0
    assert "stockout_risk" in body
    assert body["coverage"]
    assert body["by_category"]


def test_replenishment_slice_endpoint():
    response = client.get("/replenishment/slice", params={"limit": 5})
    assert response.status_code == 200
    body = response.json()
    assert "scope" in body
    assert "evidence" in body
    assert body["dashboard"]["skus"] > 0
    assert len(body["purchase_list"]) <= 5
    assert isinstance(body["suggested_filters"], list)


def test_slice_with_category_filter():
    root = client.get("/replenishment/slice", params={"limit": 25}).json()
    if not root["dashboard"]["by_category"]:
        return
    cat = root["dashboard"]["by_category"][0]["category"]
    filtered = client.get(
        "/replenishment/slice",
        params={"category": cat, "limit": 25},
    ).json()
    assert filtered["dashboard"]["skus"] <= root["dashboard"]["skus"]
    assert cat in filtered["scope"]["categories"]


def test_slice_empty_category_returns_200():
    response = client.get(
        "/replenishment/slice",
        params={"category": "__no_such_category__", "limit": 5},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["purchase_list"] == []
    assert "Ningún producto" in body["evidence"]


def test_csv_matches_filtered_list():
    root = client.get("/replenishment/slice", params={"limit": 3}).json()
    if not root["dashboard"]["by_category"]:
        return
    cat = root["dashboard"]["by_category"][0]["category"]
    params = {"category": cat, "limit": 3}
    json_items = client.get("/replenishment/purchase-list", params=params).json()
    import csv
    import io

    csv_resp = client.get("/replenishment/purchase-list.csv", params=params)
    rows = list(csv.reader(io.StringIO(csv_resp.text)))
    assert len(rows) == len(json_items) + 1
    for i, item in enumerate(json_items):
        assert rows[i + 1][1] == item["product_id"]
        assert int(rows[i + 1][4]) == item["recommended_quantity"]


def test_purchase_list_csv():
    import csv
    import io

    response = client.get("/replenishment/purchase-list.csv", params={"limit": 3})
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    rows = list(csv.reader(io.StringIO(response.text)))
    assert rows[0] == [
        "barcode",
        "product_id",
        "product_name",
        "supplier",
        "recommended_quantity",
        "operational_priority",
        "estimated_purchase_value",
    ]
    assert len(rows) == 4  # header + 3 rows
    json_items = client.get("/replenishment/purchase-list", params={"limit": 3}).json()
    for i, item in enumerate(json_items):
        assert rows[i + 1][1] == item["product_id"]
        assert int(rows[i + 1][4]) == item["recommended_quantity"]


def test_chat_purchase_list():
    response = client.post(
        "/chat",
        json={"message": "¿Qué productos tengo que comprar?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "list"
    assert body["purchase_list"]
    assert len(body["purchase_list"]) <= 25
    assert body["purchase_list"][0]["product_id"]
    dash = body["dashboard"]
    assert dash["skus"] > 0
    assert "stockout_risk" in dash
    assert "understock" in dash
    assert dash["coverage"]
    assert dash["by_category"]


def test_chat_top_categories():
    response = client.post(
        "/chat",
        json={"message": "cuales son las categorias mas vendidas"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "sales"
    assert body["dashboard"]["by_sales"]
    assert body["dashboard"]["by_sales"][0]["units_sold"] > 0
