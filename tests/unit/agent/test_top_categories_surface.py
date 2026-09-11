"""Sales ranking payload must carry the recorte its dashboard was computed from."""

from __future__ import annotations

import pytest

from app.agent.runner import _run_purchase_list, _run_top_categories
from app.core.models import ChatResponse


def _assert_dashboard_carries_scope(response: ChatResponse) -> None:
    if response.dashboard is not None:
        assert response.scope is not None, (
            f"{response.mode} carried a dashboard without a scope"
        )


@pytest.mark.asyncio
async def test_sales_turn_returns_scope_with_its_dashboard():
    response = await _run_top_categories()
    assert response.mode == "sales"
    assert response.dashboard is not None
    assert response.dashboard.by_sales
    assert response.scope is not None
    assert response.scope.categories == []
    assert response.scope.subcategories == []
    assert response.scope.health_buckets == []
    assert response.scope.suppliers == []
    assert response.scope.name_tokens == []
    _assert_dashboard_carries_scope(response)


@pytest.mark.asyncio
async def test_purchase_list_turn_also_pairs_dashboard_with_scope():
    """Triangulation: the invariant is about payload shape, not the sales mode string."""
    response = await _run_purchase_list("qué productos tengo que comprar")
    assert response.mode == "list"
    assert response.dashboard is not None
    _assert_dashboard_carries_scope(response)
