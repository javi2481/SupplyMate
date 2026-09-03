import pytest

from app.agent.intents import (
    is_purchase_list_query,
    is_top_categories_query,
    match_rule_intent,
    parse_intent_label,
)
from app.services import catalog_service


@pytest.mark.parametrize(
    "message",
    [
        "que productos tengo que comprar",
        "¿Qué productos tengo que comprar?",
        "que debo pedir",
        "qué necesito reponer",
        "que productos tengo que comprra",
        "dashboard",
        "qué está pasando",
        "salud de inventario",
        "que productos son lso que estan en falta",
        "qué productos están en falta",
        "productos sin stock",
    ],
)
def test_purchase_list_intent(message: str):
    assert is_purchase_list_query(message)


def test_purchase_list_not_triggered_for_product_name():
    assert not is_purchase_list_query("cuanto pedir de 47 street aura")


@pytest.mark.parametrize(
    "message",
    [
        "cuales son las categorias mas vendidas",
        "¿Cuáles son las categorías más vendidas?",
        "que categoria vende mas",
    ],
)
def test_top_categories_intent(message: str):
    assert is_top_categories_query(message)
    assert not is_purchase_list_query(message)


def test_list_purchase_recommendations_sorted():
    items = catalog_service.list_purchase_recommendations(limit=5)
    assert len(items) == 5
    assert items[0].recommended_quantity >= items[-1].recommended_quantity
    assert all(i.recommended_quantity > 0 for i in items)


def test_format_purchase_list_empty():
    text = catalog_service.format_purchase_list_answer([])
    assert "no hay productos" in text.lower()


@pytest.mark.parametrize(
    "message,expected",
    [
        ("qué me está faltando", None),
        ("los que se van a acabar", None),
        ("cuales estan por reventar", None),
        ("qué productos están en falta", "purchase_list"),
        ("cuales son las categorias mas vendidas", "sales_categories"),
        ("cuanto pedir de 47 street aura", None),
    ],
)
def test_rule_intent_does_not_cover_every_paraphrase(message: str, expected: str | None):
    assert match_rule_intent(message) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("purchase_list", "purchase_list"),
        ("purchase_list\nporque pregunta por falta de stock", "purchase_list"),
        ("La etiqueta es: purchase_list", "purchase_list"),
        ("inventory_health", "purchase_list"),
        ("top_categories", "sales_categories"),
        ("single_sku", "single_product"),
        ("hola, no sé", "unknown"),
        ("", "unknown"),
    ],
)
def test_parse_intent_label(raw: str, expected: str):
    assert parse_intent_label(raw) == expected
