from app.core.models import AnalyzeResponse, AnalyticalScope
from app.services import insight_cache


def test_insight_cache_hit_miss_and_reset():
    insight_cache.reset()
    scope = AnalyticalScope()
    key = insight_cache.cache_key("explore", "k1", "e1")
    assert insight_cache.get(key) is None

    response = AnalyzeResponse(
        mode="explore",
        scope=scope,
        evidence="x",
        dashboard=catalog_service_dashboard(),
        insight_source="fallback",
    )
    insight_cache.set(key, response)
    assert insight_cache.get(key) is not None
    insight_cache.reset()
    assert insight_cache.get(key) is None


def catalog_service_dashboard():
    from app.services import catalog_service

    dash, _ = catalog_service.chat_dashboard(limit=1)
    return dash
