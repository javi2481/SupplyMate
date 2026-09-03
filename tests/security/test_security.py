from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.middleware.rate_limit import reset_rate_limits
from app.services import catalog_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean_rate_limits():
    reset_rate_limits()
    yield
    reset_rate_limits()


def test_security_headers_present():
    response = client.get("/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"


def test_chat_message_too_long_returns_422():
    response = client.post("/chat", json={"message": "x" * 2001})
    assert response.status_code == 422


def test_oversized_scope_param_rejected():
    response = client.get(
        "/replenishment/slice",
        params={"category": "x" * 201, "limit": 3},
    )
    assert response.status_code == 422


def test_production_error_hides_traceback(monkeypatch):
    monkeypatch.setattr("app.middleware.safe_errors.is_production", lambda: True)
    with patch.object(
        catalog_service,
        "search_products",
        side_effect=RuntimeError("secret internal boom"),
    ):
        response = client.get("/products/search", params={"q": "test"})
    assert response.status_code == 500
    body = response.json()
    assert body["detail"] == "Internal server error"
    assert "secret" not in response.text
    assert "Traceback" not in response.text


def test_chat_rate_limit_returns_429(monkeypatch):
    monkeypatch.setattr("app.middleware.chat_rate_limit.effective_chat_rate_limit", lambda: 2)
    reset_rate_limits()
    payload = {"message": "hola"}
    with patch("app.api.run_supplymate", new=AsyncMock(return_value=_minimal_chat())):
        assert client.post("/chat", json=payload).status_code == 200
        assert client.post("/chat", json=payload).status_code == 200
        assert client.post("/chat", json=payload).status_code == 429


def test_health_not_rate_limited(monkeypatch):
    monkeypatch.setattr("app.middleware.chat_rate_limit.effective_chat_rate_limit", lambda: 1)
    reset_rate_limits()
    with patch("app.api.run_supplymate", new=AsyncMock(return_value=_minimal_chat())):
        client.post("/chat", json={"message": "one"})
        client.post("/chat", json={"message": "two"})
        assert client.post("/chat", json={"message": "three"}).status_code == 429
    for _ in range(5):
        assert client.get("/health").status_code == 200


def _minimal_chat():
    from app.core.models import ChatResponse

    return ChatResponse(answer="ok", mode="list")
