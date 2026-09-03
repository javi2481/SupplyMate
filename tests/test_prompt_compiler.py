from app.models import AnalyticalScope, InteractionEvent
from app.services import catalog_service, prompt_compiler


def test_compile_explore_prompt_includes_history_and_delta():
    scope = AnalyticalScope()
    slice_data = catalog_service.replenishment_slice(scope, limit=5)
    root_dash, _ = catalog_service.chat_dashboard(limit=1, scope=AnalyticalScope())
    events = [
        InteractionEvent(
            source="chart_category",
            action="add_filter",
            dimension="category",
            value="Perfumería",
            label_human="Perfumería",
        )
    ]
    prompt = prompt_compiler.compile_analyze_prompt(
        mode="explore",
        root_question="¿Qué comprar?",
        events=events,
        slice_data=slice_data,
        root_dashboard=root_dash,
    )
    assert "¿Qué comprar?" in prompt
    assert "Perfumería" in prompt
    assert "delta_vs_root" in prompt
    assert "DashboardInsight" in prompt
    assert "Caveat:" in prompt
    assert "Riesgo de quiebre" in prompt


def test_compile_commit_prompt_mentions_commit_summary():
    scope = AnalyticalScope()
    slice_data = catalog_service.replenishment_slice(scope, limit=3)
    root_dash, _ = catalog_service.chat_dashboard(limit=1, scope=AnalyticalScope())
    prompt = prompt_compiler.compile_analyze_prompt(
        mode="commit",
        root_question="",
        events=[],
        slice_data=slice_data,
        root_dashboard=root_dash,
    )
    assert "CommitSummary" in prompt
    assert "ARMAR OC" in prompt


def test_prompt_hash_stable():
    a = prompt_compiler.prompt_hash("same")
    b = prompt_compiler.prompt_hash("same")
    assert a == b
    assert a != prompt_compiler.prompt_hash("other")


def test_compile_explore_prompt_includes_related_for_mission_scope():
    from app.missions import load_missions

    load_missions.cache_clear()
    scope = AnalyticalScope(subcategories=["Pañales P/Bebes"], name_tokens=["xxg"])
    slice_data = catalog_service.replenishment_slice(scope, limit=5)
    root_dash, _ = catalog_service.chat_dashboard(limit=1, scope=AnalyticalScope())
    prompt = prompt_compiler.compile_analyze_prompt(
        mode="explore",
        root_question="¿Cuántos pañales?",
        events=[],
        slice_data=slice_data,
        root_dashboard=root_dash,
    )
    assert '"related"' in prompt
    assert "Toallitas húmedas" in prompt
    assert "higiene" in prompt
    assert "co-ocurrencia transaccional" in prompt
