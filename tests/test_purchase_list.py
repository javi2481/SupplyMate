import pytest

from app.intents import is_purchase_list_query
from app.services import catalog_service


@pytest.mark.parametrize(
    "message",
    [
        "que productos tengo que comprar",
        "¿Qué productos tengo que comprar?",
        "que debo pedir",
        "qué necesito reponer",
        "que productos tengo que comprra",
    ],
)
def test_purchase_list_intent(message: str):
    assert is_purchase_list_query(message)


def test_purchase_list_not_triggered_for_product_name():
    assert not is_purchase_list_query("cuanto pedir de 47 street aura")


def test_list_purchase_recommendations_sorted():
    items = catalog_service.list_purchase_recommendations(limit=5)
    assert len(items) == 5
    assert items[0].recommended_quantity >= items[-1].recommended_quantity
    assert all(i.recommended_quantity > 0 for i in items)


def test_format_purchase_list_empty():
    text = catalog_service.format_purchase_list_answer([])
    assert "no hay productos" in text.lower()
