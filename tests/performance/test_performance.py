import time

import pytest

from app.core.models import AnalyticalScope
from app.services import catalog_service

pytestmark = pytest.mark.performance


def test_replenishment_slice_under_threshold():
    scope = AnalyticalScope()
    start = time.perf_counter()
    catalog_service.replenishment_slice(scope, limit=100)
    elapsed = time.perf_counter() - start
    assert elapsed < 3.0, f"slice took {elapsed:.2f}s"


def test_chat_dashboard_under_threshold():
    scope = AnalyticalScope()
    start = time.perf_counter()
    catalog_service.chat_dashboard(limit=100, scope=scope)
    elapsed = time.perf_counter() - start
    assert elapsed < 3.0, f"chat_dashboard took {elapsed:.2f}s"
