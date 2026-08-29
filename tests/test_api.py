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
    assert body["recommended_quantity"] == 172
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
    assert body["recommended_quantity"] == 172
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
