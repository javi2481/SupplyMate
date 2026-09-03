"""Unit tests for guidance preview helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.core.models import AnalyticalScope, InventoryDashboard, PurchaseListItem
from app.guidance.engine import preview_union
from app.guidance.missions import MissionEdge


def test_preview_union_calls_chat_dashboard_once():
    dash = InventoryDashboard(
        skus=12,
        stockout_risk=2,
        estimated_purchase_value=150.0,
    )
    items = [
        PurchaseListItem(
            product_id="1",
            product_name="A",
            recommended_quantity=5,
        )
    ]
    mock_chat = MagicMock(return_value=(dash, items))
    edge = MissionEdge(
        from_group="panales",
        from_dimension="subcategory",
        to_group="mamaderas",
        to_dimension="name_token",
        mission="bebe",
        reason="complement",
        label="Mamaderas",
    )
    with patch(
        "app.services.analytics.catalog_service.chat_dashboard",
        mock_chat,
    ):
        result = preview_union(AnalyticalScope(subcategories=["Pañales P/Bebes"]), edge)

    assert mock_chat.call_count == 1
    assert result == {"skus": 12, "qty": 5, "value": 150.0}
    assert "added_skus" not in result
