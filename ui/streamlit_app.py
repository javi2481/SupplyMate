"""SupplyMate · Operación — Streamlit assistant (FastAPI /chat + OC export)."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import altair as alt
import httpx
import streamlit as st

from app.core.models import AnalyticalScope, GuidanceChip, InteractionEvent
from app.services import dashboard as dash_svc
from app.services import metrics, suggested_filters
from app.services import panel_modes
from app.services import scope as scope_svc
from ui import analyst as analyst_mod
from ui import charts
from ui import chrome
from ui import components
from ui import layout_commit
from ui import layout_explore
from ui import theme as theme_mod
from ui.composition import chat_policy as chat_policy_mod
from ui.composition import copy as ui_copy
from ui.composition import kpi_policy as kpi_policy_mod
from ui.composition import next_step as next_step_mod
from ui.composition import scope_label as scope_label_mod
from ui.composition import table_policy as table_policy_mod
from ui import threads as threads_mod
from ui.threads import rail as threads_rail_mod

# Streamlit keeps sys.modules across reruns; sibling UI modules go stale.
metrics = importlib.reload(metrics)
dash_svc = importlib.reload(dash_svc)
ui_copy = importlib.reload(ui_copy)
kpi_policy_mod = importlib.reload(kpi_policy_mod)
table_policy_mod = importlib.reload(table_policy_mod)
scope_label_mod = importlib.reload(scope_label_mod)
next_step_mod = importlib.reload(next_step_mod)
chat_policy_mod = importlib.reload(chat_policy_mod)
threads_mod = importlib.reload(threads_mod)
threads_rail_mod = importlib.reload(threads_rail_mod)
theme_mod = importlib.reload(theme_mod)
charts = importlib.reload(charts)
components = importlib.reload(components)
chrome = importlib.reload(chrome)
analyst_mod = importlib.reload(analyst_mod)
layout_explore = importlib.reload(layout_explore)
layout_commit = importlib.reload(layout_commit)
ThreadStore = threads_mod.ThreadStore
apply_snapshot = threads_mod.apply_snapshot
persist_active = threads_mod.persist_active
prepare_new_chat = threads_mod.prepare_new_chat
switch_thread = threads_mod.switch_thread
compose_next_step = next_step_mod.compose_next_step
NextStepOption = next_step_mod.NextStepOption
chat_would_unfreeze = chat_policy_mod.chat_would_unfreeze
is_transport_error_message = chat_policy_mod.is_transport_error_message
live_dashboard_index = chat_policy_mod.live_dashboard_index
should_skip_repeat_purchase_query = chat_policy_mod.should_skip_repeat_purchase_query
hide_history_message = chat_policy_mod.hide_history_message

API_URL = os.getenv("SUPPLYMATE_API_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_option("client.toolbarMode", "viewer")
st.set_page_config(
    page_title="SupplyMate",
    layout="wide",
    page_icon="📦",
    initial_sidebar_state="expanded",
)
components.inject_theme()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None
if "live_list_active" not in st.session_state:
    st.session_state.live_list_active = False
if "analytical_scope" not in st.session_state:
    st.session_state.analytical_scope = scope_svc.empty_scope().model_dump()
if "slice_data" not in st.session_state:
    st.session_state.slice_data = None
if "highlight_calc" not in st.session_state:
    st.session_state.highlight_calc = None
if "panel_mode" not in st.session_state:
    st.session_state.panel_mode = "explore"
if "frozen_scope" not in st.session_state:
    st.session_state.frozen_scope = None
if "interaction_events" not in st.session_state:
    st.session_state.interaction_events = []
if "root_question" not in st.session_state:
    st.session_state.root_question = ""
if "analyst_enabled" not in st.session_state:
    st.session_state.analyst_enabled = True
if "analyze_data" not in st.session_state:
    st.session_state.analyze_data = None
if "last_analyze_key" not in st.session_state:
    st.session_state.last_analyze_key = ""
if "guidance" not in st.session_state:
    st.session_state.guidance = None
if "pending_unfreeze" not in st.session_state:
    st.session_state.pending_unfreeze = None
if "root_skus" not in st.session_state:
    st.session_state.root_skus = None
if "active_thread_id" not in st.session_state:
    st.session_state.active_thread_id = None
if "threads_hydrated" not in st.session_state:
    st.session_state.threads_hydrated = False


def _threads_path() -> Path:
    raw = os.getenv("SUPPLYMATE_THREADS_PATH")
    return Path(raw) if raw else threads_mod.DEFAULT_STORE_PATH


def _thread_store() -> ThreadStore:
    return ThreadStore(_threads_path())


def _autosave() -> None:
    persist_active(_thread_store(), st.session_state)


def _hydrate_threads() -> None:
    if st.session_state.threads_hydrated:
        return
    st.session_state.threads_hydrated = True
    store = _thread_store()
    if not store.active_id:
        return
    thread = store.get(store.active_id)
    if thread is None:
        return
    apply_snapshot(st.session_state, thread.snapshot)
    st.session_state.active_thread_id = thread.id


def _append_event(
    *,
    source: str,
    action: str,
    dimension: str = "",
    value: str = "",
    label_human: str = "",
) -> None:
    st.session_state.interaction_events.append(
        InteractionEvent(
            source=source,
            action=action,
            dimension=dimension,
            value=value,
            label_human=label_human,
        ).model_dump()
    )


def _effective_panel_scope() -> AnalyticalScope:
    if st.session_state.panel_mode == "commit" and st.session_state.frozen_scope:
        return AnalyticalScope.model_validate(st.session_state.frozen_scope)
    return _scope_model()


def _enter_commit_mode() -> None:
    scope = _scope_model()
    st.session_state.frozen_scope = scope.model_dump()
    st.session_state.panel_mode = "commit"
    _append_event(
        source="mode_transition",
        action="enter_commit",
        label_human="Listo — armar OC de este recorte",
    )
    st.session_state.last_analyze_key = ""
    _autosave()


def _exit_commit_mode() -> None:
    st.session_state.panel_mode = "explore"
    st.session_state.frozen_scope = None
    _append_event(
        source="mode_transition",
        action="exit_commit",
        label_human="Volver a explorar",
    )
    st.session_state.last_analyze_key = ""
    _autosave()


def fetch_analyze(scope: AnalyticalScope, *, mode: str) -> dict | None:
    events = [
        InteractionEvent.model_validate(e) for e in st.session_state.interaction_events
    ]
    body: dict = {
        "mode": mode,
        "scope": scope.model_dump(),
        "events": [e.model_dump() for e in events],
        "root_question": st.session_state.root_question,
        "insight_level": "full",
    }
    if mode == "commit" and st.session_state.frozen_scope:
        body["frozen_scope"] = st.session_state.frozen_scope
    try:
        response = httpx.post(
            f"{API_URL}/replenishment/analyze",
            json=body,
            timeout=180.0,
        )
        if response.status_code == 200:
            return response.json()
    except httpx.ConnectError:
        return None
    return None


def _analyze_cache_key(scope: AnalyticalScope, mode: str) -> str:
    ev_len = len(st.session_state.interaction_events)
    return f"{mode}|{scope_svc.cache_key(scope)}|{ev_len}"


def _scope_model() -> AnalyticalScope:
    return AnalyticalScope.model_validate(st.session_state.analytical_scope)


def _set_scope(scope: AnalyticalScope) -> None:
    st.session_state.analytical_scope = scope.model_dump()


def scope_query_params(scope: AnalyticalScope, *, limit: int = 25) -> list[tuple[str, str]]:
    params: list[tuple[str, str]] = [("limit", str(limit))]
    for cat in scope.categories:
        params.append(("category", cat))
    for sub in scope.subcategories:
        params.append(("subcategory", sub))
    for bucket in scope.coverage_buckets:
        params.append(("coverage_bucket", bucket))
    for health in scope.health_buckets:
        params.append(("health_bucket", health))
    for supplier in scope.suppliers:
        params.append(("supplier", supplier))
    for token in scope.name_tokens:
        params.append(("name_token", token))
    if scope.highlight_product_id:
        params.append(("highlight_product_id", scope.highlight_product_id))
    return params


def fetch_slice(scope: AnalyticalScope, limit: int = 25) -> dict | None:
    try:
        response = httpx.get(
            f"{API_URL}/replenishment/slice",
            params=scope_query_params(scope, limit=limit),
            timeout=120.0,
        )
        if response.status_code == 200:
            return response.json()
    except httpx.ConnectError:
        return None
    return None


def _slice_from_chat(data: dict) -> dict | None:
    dashboard = data.get("dashboard")
    if not dashboard:
        return None
    return {
        "dashboard": dashboard,
        "purchase_list": data.get("purchase_list") or [],
        "evidence": "",
        "guidance": data.get("guidance"),
        "suggested_filters": data.get("suggested_filters") or [],
    }


def _slice_from_last_assistant_message() -> dict | None:
    for msg in reversed(st.session_state.messages):
        if msg.get("role") != "assistant" or msg.get("mode") not in ("list", "explore"):
            continue
        dashboard = msg.get("dashboard")
        if not dashboard:
            continue
        return {
            "dashboard": dashboard,
            "purchase_list": msg.get("purchase_list") or [],
            "evidence": "",
            "guidance": msg.get("guidance"),
            "suggested_filters": msg.get("suggested_filters") or [],
        }
    return None


def _dashboard_has_charts(dashboard: dict | None) -> bool:
    dash = dashboard or {}
    return bool(dash.get("by_category") or dash.get("coverage"))


def _merge_dashboard_charts(slice_data: dict, messages: list[dict]) -> dict:
    dash = dict(slice_data.get("dashboard") or {})
    if _dashboard_has_charts(dash):
        return slice_data
    for msg in reversed(messages):
        if msg.get("role") != "assistant" or msg.get("mode") not in ("list", "explore"):
            continue
        alt = msg.get("dashboard") or {}
        if not dash.get("by_category") and alt.get("by_category"):
            dash["by_category"] = alt["by_category"]
        if not dash.get("coverage") and alt.get("coverage"):
            dash["coverage"] = alt["coverage"]
        if _dashboard_has_charts(dash):
            break
    merged = dict(slice_data)
    merged["dashboard"] = dash
    return merged


def _resolve_live_slice(scope: AnalyticalScope) -> dict | None:
    slice_data = fetch_slice(scope, limit=25)
    if slice_data is None:
        slice_data = st.session_state.slice_data
    if slice_data is None:
        slice_data = _slice_from_last_assistant_message()
    if slice_data is None:
        return None
    return _merge_dashboard_charts(slice_data, st.session_state.messages)


def fetch_purchase_csv(scope: AnalyticalScope, limit: int = 25) -> bytes | None:
    try:
        response = httpx.get(
            f"{API_URL}/replenishment/purchase-list.csv",
            params=scope_query_params(scope, limit=limit),
            timeout=120.0,
        )
        if response.status_code == 200:
            return response.content
    except httpx.ConnectError:
        return None
    return None


def fetch_replenishment(product_id: str) -> dict | None:
    try:
        response = httpx.get(
            f"{API_URL}/products/{product_id}/replenishment",
            timeout=60.0,
        )
        if response.status_code == 200:
            return response.json()
    except httpx.ConnectError:
        return None
    return None


def apply_guidance_chip_action(chip_data: dict) -> None:
    """Apply a validated guidance chip without re-interpreting through the LLM."""
    from app.guidance.guidance_chips import apply_guidance_chip

    chip = GuidanceChip.model_validate(chip_data)
    scope = _scope_model()
    new_scope, enter_commit = apply_guidance_chip(scope, chip)
    _set_scope(new_scope)
    _append_event(
        source="chip",
        action="add_filter",
        label_human=chip.label,
    )
    st.session_state.last_analyze_key = ""
    if enter_commit:
        _enter_commit_mode()
    slice_data = fetch_slice(new_scope)
    if slice_data:
        st.session_state.slice_data = slice_data
        st.session_state.guidance = slice_data.get("guidance")
    _autosave()


def apply_filter_action(action: str, args: dict[str, str], *, source: str = "chip") -> None:
    scope = _scope_model()
    if action == suggested_filters.ACTION_FILTER_CATEGORY:
        cat = args["category"]
        scope = scope_svc.add(scope, "category", cat)
        _append_event(
            source=source,
            action="add_filter",
            dimension="category",
            value=cat,
            label_human=cat,
        )
    elif action == suggested_filters.ACTION_FILTER_COVERAGE:
        bucket = args["coverage_bucket"]
        scope = scope_svc.add(scope, "coverage_bucket", bucket)
        _append_event(
            source=source,
            action="add_filter",
            dimension="coverage_bucket",
            value=bucket,
            label_human=bucket,
        )
    elif action == suggested_filters.ACTION_FILTER_HEALTH:
        health = args["health_bucket"]
        scope = scope_svc.add(scope, "health_bucket", health)
        _append_event(
            source=source,
            action="add_filter",
            dimension="health_bucket",
            value=health,
            label_human=health,
        )
    elif action == suggested_filters.ACTION_FILTER_SUPPLIER:
        supplier = args["supplier"]
        scope = scope_svc.add(scope, "supplier", supplier)
        _append_event(
            source=source,
            action="add_filter",
            dimension="supplier",
            value=supplier,
            label_human=supplier,
        )
    elif action == suggested_filters.ACTION_FILTER_NAME_TOKEN:
        token = args["name_token"]
        scope = scope_svc.add(scope, "name_token", token)
        _append_event(
            source=source,
            action="add_filter",
            dimension="name_token",
            value=token,
            label_human=token.upper() if token.islower() else token,
        )
    elif action == suggested_filters.ACTION_OPEN_SKU:
        pid = args["product_id"]
        scope = scope_svc.set_highlight(scope, pid)
        calc = fetch_replenishment(pid)
        st.session_state.highlight_calc = calc
        _append_event(
            source=source,
            action="highlight_sku",
            dimension="product_id",
            value=pid,
            label_human=f"SKU {pid}",
        )
        _set_scope(scope)
        st.session_state.last_analyze_key = ""
        _autosave()
        return
    scope = scope_svc.clear_highlight(scope)
    st.session_state.highlight_calc = None
    _set_scope(scope)
    st.session_state.last_analyze_key = ""
    _autosave()


def _breadcrumb_labels(scope: AnalyticalScope) -> list[tuple[str, str, str]]:
    crumbs: list[tuple[str, str, str]] = [("root", "Inventario", "")]
    for cat in scope.categories:
        crumbs.append(("category", cat, cat))
    for sub in scope.subcategories:
        crumbs.append(("subcategory", sub, sub))
    for bucket in scope.coverage_buckets:
        crumbs.append(("coverage_bucket", bucket, bucket))
    for health in scope.health_buckets:
        label = metrics.BUCKET_LABELS.get(health, health)
        crumbs.append(("health_bucket", health, label))
    for supplier in scope.suppliers:
        crumbs.append(("supplier", supplier, supplier))
    for token in scope.name_tokens:
        crumbs.append(("name_token", token, token.upper() if token.islower() else token))
    if scope.highlight_product_id:
        crumbs.append(("highlight", scope.highlight_product_id, f"SKU {scope.highlight_product_id}"))
    return crumbs


def render_breadcrumb(scope: AnalyticalScope, *, readonly: bool = False) -> None:
    st.markdown("**Analizando:**")
    cols = st.columns([6, 1])
    with cols[0]:
        parts = []
        for kind, value, label in _breadcrumb_labels(scope):
            if kind == "root":
                parts.append(label)
            else:
                parts.append(label)
        st.caption(" › ".join(parts) if parts else "Inventario")
    with cols[1]:
        if not readonly and st.button("Limpiar filtros", key="reset_scope"):
            _set_scope(scope_svc.reset())
            st.session_state.highlight_calc = None
            st.session_state.interaction_events = []
            _append_event(source="reset", action="reset", label_human="Limpiar filtros")
            st.session_state.last_analyze_key = ""
            _autosave()
            st.rerun()

    if readonly:
        return

    remove_cols = st.columns(8)
    idx = 0
    for kind, value, label in _breadcrumb_labels(scope):
        if kind == "root":
            continue
        if idx < len(remove_cols) and remove_cols[idx].button(f"{label} ×", key=f"rm-{kind}-{value}"):
            current = _scope_model()
            if kind == "highlight":
                current = scope_svc.clear_highlight(current)
                st.session_state.highlight_calc = None
                _append_event(
                    source="breadcrumb",
                    action="remove_filter",
                    dimension="highlight",
                    value=value,
                    label_human=label,
                )
            else:
                current = scope_svc.remove(current, kind, value)
                _append_event(
                    source="breadcrumb",
                    action="remove_filter",
                    dimension=kind,
                    value=value,
                    label_human=label,
                )
            _set_scope(current)
            st.session_state.last_analyze_key = ""
            _autosave()
            st.rerun()
        idx += 1


def render_inventory_dashboard_static(dash: dict | None, purchase_list: list[dict]) -> None:
    dash = dash or {}
    components.render_kpi_strip(dash, purchase_lines=len(purchase_list))
    components.render_health_legend()
    components.render_coverage_strip(dash.get("coverage") or [])

    category_rows = dash.get("by_category") or []
    coverage_rows = dash.get("coverage") or []
    left, right = st.columns(2)
    with left:
        st.markdown(f"**{metrics.LABEL_RECOMMENDED_QTY} por categoría**")
        st.caption("Click en una barra para filtrar (solo en panel vivo)")
        if category_rows:
            st.altair_chart(
                charts.lollipop(
                    category_rows,
                    "category",
                    "Categoría",
                    extra_tooltips=[alt.Tooltip("sku_count:Q", title="Productos")],
                ),
                width="stretch",
            )
    with right:
        st.markdown(f"**Distribución de {metrics.LABEL_COVERAGE}**")
        st.caption("Rojo = pocos días de stock · Verde = holgado")
        if coverage_rows:
            st.altair_chart(
                charts.histogram(
                    coverage_rows,
                    "bucket",
                    metrics.LABEL_COVERAGE,
                    x_sort=list(dash_svc.COVERAGE_ORDER),
                ),
                width="stretch",
            )

    if purchase_list:
        components.render_oc_summary(purchase_list)
        components.render_purchase_table(purchase_list, selectable=False)


def render_live_panel() -> None:
    panel_mode = st.session_state.panel_mode
    explore_mode = panel_mode == "explore"
    scope = _effective_panel_scope()
    mutable_scope = _scope_model()

    slice_data = st.session_state.slice_data
    if not slice_data:
        slice_data = _resolve_live_slice(scope)
    if slice_data is None:
        st.error(f"No pude conectar con la API en `{API_URL}`. Arrancá uvicorn primero.")
        return
    st.session_state.slice_data = slice_data
    st.session_state.guidance = slice_data.get("guidance")
    dash = slice_data.get("dashboard") or {}
    if st.session_state.root_skus is None:
        skus = dash.get("skus")
        if isinstance(skus, int):
            st.session_state.root_skus = skus

    analyze_key = _analyze_cache_key(scope, panel_mode)
    if st.session_state.analyst_enabled and analyze_key != st.session_state.last_analyze_key:
        analyze_body = fetch_analyze(_scope_model(), mode=panel_mode)
        if analyze_body:
            st.session_state.analyze_data = analyze_body
            st.session_state.last_analyze_key = analyze_key
    analyze_data = st.session_state.analyze_data or {}
    insight = analyze_data.get("insight") or {}
    next_step = compose_next_step(
        slice_data.get("guidance"),
        slice_data.get("suggested_filters"),
        insight.get("suggested_questions") or [],
    )

    def _on_option(opt: NextStepOption) -> None:
        if opt.kind == "guidance" and opt.guidance_chip:
            apply_guidance_chip_action(opt.guidance_chip)
        elif opt.kind == "filter" and opt.filter_action:
            apply_filter_action(opt.filter_action, opt.filter_args or {}, source="chip")
        elif opt.kind == "prompt":
            st.session_state.pending_prompt = opt.label

    def _on_prompt(text: str) -> None:
        st.session_state.pending_prompt = text

    def _on_reset() -> None:
        _set_scope(scope_svc.reset())
        st.session_state.highlight_calc = None
        st.session_state.interaction_events = []
        st.session_state.root_skus = None
        _append_event(source="reset", action="reset", label_human="Limpiar")
        st.session_state.last_analyze_key = ""
        _autosave()

    def _on_category(cat: str) -> None:
        _set_scope(scope_svc.add(mutable_scope, "category", cat))
        _append_event(
            source="chart_category",
            action="add_filter",
            dimension="category",
            value=cat,
            label_human=cat,
        )
        st.session_state.last_analyze_key = ""
        _autosave()

    def _on_coverage(bucket: str) -> None:
        _set_scope(scope_svc.add(mutable_scope, "coverage_bucket", bucket))
        _append_event(
            source="chart_coverage",
            action="add_filter",
            dimension="coverage_bucket",
            value=bucket,
            label_human=bucket,
        )
        st.session_state.last_analyze_key = ""
        _autosave()

    def _on_sku(sku: str) -> None:
        apply_filter_action(
            suggested_filters.ACTION_OPEN_SKU,
            {"product_id": sku},
            source="table_row",
        )

    if explore_mode:
        layout_explore.render_explore_panel(
            scope=scope,
            slice_data=slice_data,
            analyze_data=analyze_data,
            next_step=next_step,
            interaction_events=st.session_state.interaction_events,
            highlight_calc=st.session_state.highlight_calc,
            analyst_enabled=st.session_state.analyst_enabled,
            root_skus=st.session_state.root_skus,
            on_option=_on_option,
            on_prompt=_on_prompt,
            on_reset=_on_reset,
            on_category=_on_category,
            on_coverage=_on_coverage,
            on_sku=_on_sku,
            on_enter_commit=_enter_commit_mode,
            table_selection_sku=_table_selection_sku,
            render_calculation=render_calculation,
        )
    else:
        purchase_list = slice_data.get("purchase_list") or []
        csv_bytes = fetch_purchase_csv(scope, limit=max(len(purchase_list), 1))
        layout_commit.render_commit_panel(
            scope=scope,
            slice_data=slice_data,
            analyze_data=analyze_data,
            analyst_enabled=st.session_state.analyst_enabled,
            csv_bytes=csv_bytes if panel_modes.can_export(panel_mode) else None,
            on_exit=_exit_commit_mode,
            on_reanalyze=lambda: st.session_state.__setitem__("last_analyze_key", ""),
        )
    _autosave()


def _handle_sidebar() -> None:
    with st.sidebar:
        store = _thread_store()
        store.refresh_all_labels()
        action = chrome.render_thread_rail(
            store,
            active_id=st.session_state.get("active_thread_id"),
        )
        if action is None:
            return
        if action.kind == "new_chat":
            prepare_new_chat(store, st.session_state)
            st.rerun()
        if action.kind == "select" and action.thread_id:
            switch_thread(store, st.session_state, action.thread_id)
            st.rerun()
        if action.kind == "pin" and action.thread_id:
            persist_active(store, st.session_state)
            store.set_pinned(action.thread_id, True)
            st.rerun()
        if action.kind == "unpin" and action.thread_id:
            store.set_pinned(action.thread_id, False)
            st.rerun()


def _table_selection_sku(event: Any, purchase_list: list[dict]) -> str | None:
    if event is None or not purchase_list:
        return None
    rows: list[int] = []
    if hasattr(event, "selection") and event.selection:
        raw = event.selection.get("rows") or []
        rows = [int(i) for i in raw if isinstance(i, int)]
    elif isinstance(event, dict):
        selection = event.get("selection") or {}
        raw = selection.get("rows") or []
        rows = [int(i) for i in raw if isinstance(i, int)]
    if not rows:
        return None
    idx = rows[0]
    if 0 <= idx < len(purchase_list):
        return str(purchase_list[idx].get("product_id") or "") or None
    return None


def render_sales_ranking(dash: dict | None) -> None:
    dash = dash or {}
    rows = dash.get("by_sales") or []
    st.caption("Categorías más vendidas (unidades, últimos 30 días)")
    if rows:
        st.altair_chart(
            charts.lollipop(
                rows,
                "category",
                "Categoría",
                x_field="units_sold",
                x_title="Unidades vendidas (30 días)",
                extra_tooltips=[alt.Tooltip("sku_count:Q", title="Productos")],
            ),
            width="stretch",
        )


def render_calculation(calc: dict) -> None:
    with st.expander("Cómo se calculó", expanded=True):
        st.markdown(
            f"""
Política **order-up-to** (horizonte 7 días + lead time + stock de seguridad).
El punto de reorden es una alarma de salud; no entra en esta cuenta.

- Demanda diaria promedio: **{calc.get("average_daily_demand", 0):.2f}**
- Demanda horizonte (7 días): **{calc.get("demand_horizon", 0):.2f}**
- Demanda en lead time: **{calc.get("demand_lead_time", 0):.2f}**
- Stock de seguridad: **{calc.get("safety_stock", 0)}**
- Objetivo de stock: **{calc.get("stock_target", 0):.2f}**
- Stock actual: **{calc.get("current_stock", 0)}**
- **Cantidad recomendada: {calc.get("recommended_quantity", 0)}** (Python, redondeo hacia arriba)
"""
        )


def _explore_summary_line(dash: dict | None, purchase_list: list[dict]) -> str:
    dash = dash or {}
    stockout = dash.get("stockout_risk")
    n = len(purchase_list)
    if stockout is not None and n:
        return f"{stockout} en riesgo de quiebre · {n} para reponer"
    if stockout is not None:
        return f"{stockout} en riesgo de quiebre"
    if n:
        return f"{n} para reponer"
    return ""


_SUMMARY_ICON = (
    '<span class="sm-chat-summary-icon" aria-hidden="true">'
    '<svg viewBox="0 0 24 24"><path d="M3 17h2v-7H3v7Zm8 0h2V7h-2v10Zm8 0h2V4h-2v13Z"/></svg>'
    "</span>"
)


def _live_summary_source() -> tuple[dict, list[dict]]:
    slice_data = st.session_state.get("slice_data") or {}
    dash = slice_data.get("dashboard") or {}
    purchase = slice_data.get("purchase_list") or []
    return dash, purchase


def render_history() -> None:
    messages = st.session_state.messages
    live = st.session_state.live_list_active
    live_idx = live_dashboard_index(messages, live=live)
    live_dash, live_purchase = _live_summary_source() if live else ({}, [])
    for i, msg in enumerate(messages):
        if hide_history_message(messages, i, live=live):
            continue
        is_live_anchor = live_idx is not None and i == live_idx
        live_dashboard_turn = (
            is_live_anchor
            and msg.get("role") == "assistant"
            and msg.get("mode") in ("list", "explore")
        )
        with st.chat_message(msg["role"]):
            if msg.get("mode") in ("list", "explore"):
                if live_dashboard_turn:
                    summary = _explore_summary_line(
                        live_dash or msg.get("dashboard"),
                        live_purchase or msg.get("purchase_list") or [],
                    )
                    if summary:
                        st.markdown(
                            f"<div class='sm-chat-summary'>{_SUMMARY_ICON}{summary}</div>",
                            unsafe_allow_html=True,
                        )
                elif not live:
                    render_inventory_dashboard_static(
                        msg.get("dashboard"),
                        msg.get("purchase_list") or [],
                    )
                    if msg.get("csv_bytes"):
                        st.download_button(
                            "Descargar orden de compra (CSV)",
                            data=msg["csv_bytes"],
                            file_name="purchase_order.csv",
                            mime="text/csv",
                            key=f"dl-{id(msg)}",
                        )
            elif msg.get("mode") == "sales":
                render_sales_ranking(msg.get("dashboard"))
            else:
                if msg.get("product_name"):
                    st.markdown(f"**{msg['product_name']}**")
                if msg.get("quantity") is not None:
                    st.metric(metrics.LABEL_RECOMMENDED_QTY, msg["quantity"])
                if msg.get("metrics"):
                    cols = st.columns(3)
                    m = msg["metrics"]
                    cols[0].metric("Stock", m.get("stock", "—"))
                    cols[1].metric("Demanda diaria", m.get("avg_daily", "—"))
                    cols[2].metric(
                        metrics.LABEL_REORDER_POINT,
                        m.get("rop", "—"),
                        help=metrics.ROP_CAPTION,
                    )
                if msg.get("calculation"):
                    render_calculation(msg["calculation"])
            if msg.get("content") and not live_dashboard_turn:
                st.markdown(msg["content"])


def _apply_explore_chat(prompt: str, data: dict, *, is_refine: bool) -> None:
    st.session_state.live_list_active = True
    st.session_state.root_question = prompt
    st.session_state.panel_mode = "explore"
    st.session_state.frozen_scope = None
    st.session_state.pending_unfreeze = None
    if not is_refine:
        st.session_state.interaction_events = []
        st.session_state.root_skus = None
    st.session_state.analyze_data = None
    st.session_state.last_analyze_key = ""
    st.session_state.guidance = data.get("guidance")
    _append_event(
        source="chat",
        action="reset" if not is_refine else "add_filter",
        label_human=prompt,
    )
    if data.get("scope"):
        _set_scope(AnalyticalScope.model_validate(data["scope"]))
    else:
        _set_scope(scope_svc.reset())
    st.session_state.highlight_calc = None
    chat_slice = _slice_from_chat(data)
    if chat_slice:
        st.session_state.slice_data = chat_slice
    _autosave()


def ask_api(prompt: str) -> dict:
    payload: dict = {"message": prompt}
    if st.session_state.live_list_active:
        payload["scope"] = _scope_model().model_dump()
    try:
        response = httpx.post(
            f"{API_URL}/chat",
            json=payload,
            timeout=180.0,
        )
    except httpx.ConnectError:
        return {
            "answer": f"No pude conectar con la API en `{API_URL}`. Arrancá uvicorn primero.",
            "mode": "error",
        }

    if response.status_code == 404:
        return {
            "answer": (
                "No encontré ese producto.\n\n"
                "Escribí el nombre del producto, o preguntá: "
                "*¿Qué productos tengo que comprar?*"
            ),
            "mode": "error",
        }
    if response.status_code >= 400:
        return {"answer": ui_copy.CHAT_CATALOG_ERROR, "mode": "error"}

    return response.json()


_hydrate_threads()

if (
    not st.session_state.messages
    and not st.session_state.live_list_active
    and not st.session_state.pending_prompt
):
    st.session_state.pending_prompt = ui_copy.DEFAULT_STARTUP_QUERY

_handle_sidebar()

chrome.render_header(
    st.session_state.panel_mode,
    live=st.session_state.live_list_active,
)
if st.session_state.live_list_active:
    primed = _resolve_live_slice(_effective_panel_scope())
    if primed:
        st.session_state.slice_data = primed
render_history()

if st.session_state.pending_unfreeze:
    st.warning(ui_copy.UNFREEZE_WARNING)
    if st.button(ui_copy.CONFIRM_UNFREEZE, key="confirm_unfreeze"):
        payload = st.session_state.pending_unfreeze
        interp = (payload.get("data") or {}).get("interpretation") or {}
        _apply_explore_chat(
            payload["prompt"],
            payload["data"],
            is_refine=interp.get("relation") == "refinement",
        )
        st.rerun()
    if st.button(ui_copy.KEEP_COMMIT, key="keep_commit"):
        st.session_state.pending_unfreeze = None
        _autosave()
        st.rerun()

if st.session_state.live_list_active:
    with st.container():
        render_live_panel()

with st.bottom:
    prompt = st.session_state.pending_prompt or st.chat_input(ui_copy.CHAT_PLACEHOLDER)
if st.session_state.pending_prompt:
    st.session_state.pending_prompt = None

if prompt:
    if should_skip_repeat_purchase_query(
        live=st.session_state.live_list_active,
        prompt=prompt,
    ):
        st.rerun()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Calculando recomendaciones..."):
            data = ask_api(prompt)

        mode = data.get("mode", "single")
        purchase_list = data.get("purchase_list") or []
        dash = data.get("dashboard")
        csv_bytes = None

        skip_tail_append = False
        if mode in ("list", "explore"):
            interp = data.get("interpretation") or {}
            is_refine = interp.get("relation") == "refinement"
            labels = interp.get("understood_labels") or []
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": data.get("answer", ""),
                    "mode": mode,
                    "purchase_list": purchase_list,
                    "dashboard": dash,
                    "understood_labels": labels,
                    "guidance_options": interp.get("guidance_options") or [],
                }
            )
            skip_tail_append = True
            if chat_would_unfreeze(st.session_state.panel_mode, mode):
                st.session_state.pending_unfreeze = {"prompt": prompt, "data": data}
                st.markdown(data.get("answer", ""))
            else:
                _apply_explore_chat(prompt, data, is_refine=is_refine)
                st.rerun()
        elif mode == "disambiguation":
            st.session_state.live_list_active = False
            interp = data.get("interpretation") or {}
            options = interp.get("disambiguation_options") or []
            if options:
                cols = st.columns(min(len(options), 3))
                for i, opt in enumerate(options[:3]):
                    with cols[i % len(cols)]:
                        if st.button(opt, key=f"disambig-{opt}-{id(prompt)}"):
                            st.session_state.pending_prompt = (
                                f"¿Cuántos {opt.lower()} debo comprar?"
                            )
                            st.rerun()
        elif mode == "sales":
            st.session_state.live_list_active = False
            render_sales_ranking(dash)
        elif mode == "single" and data.get("product_name"):
            st.session_state.live_list_active = False
            ctx = data.get("context") or {}
            calc = data.get("calculation") or {}
            st.markdown(f"**{data['product_name']}**")
            st.metric(metrics.LABEL_RECOMMENDED_QTY, data.get("recommended_quantity", 0))
            cols = st.columns(3)
            cols[0].metric("Stock", ctx.get("current_stock", "—"))
            cols[1].metric(
                "Demanda diaria",
                round(calc.get("average_daily_demand", 0), 1),
            )
            cols[2].metric(
                metrics.LABEL_REORDER_POINT,
                ctx.get("reorder_point", "—"),
                help=metrics.ROP_CAPTION,
            )
            if calc:
                render_calculation(calc)

        keep_error_turn = not (mode == "error" and st.session_state.live_list_active)
        if not skip_tail_append:
            if keep_error_turn:
                st.markdown(data.get("answer", ""))
            else:
                st.error(data.get("answer") or ui_copy.CHAT_CATALOG_ERROR)

    if not skip_tail_append and keep_error_turn:
        st.session_state.messages.append(
        {
            "role": "assistant",
            "content": data.get("answer", ""),
            "mode": data.get("mode"),
            "product_name": data.get("product_name"),
            "quantity": data.get("recommended_quantity"),
            "purchase_list": data.get("purchase_list") or [],
            "dashboard": data.get("dashboard"),
            "csv_bytes": csv_bytes,
            "calculation": data.get("calculation"),
            "metrics": (
                {
                    "stock": (data.get("context") or {}).get("current_stock"),
                    "avg_daily": round(
                        (data.get("calculation") or {}).get("average_daily_demand", 0), 1
                    ),
                    "rop": (data.get("context") or {}).get("reorder_point"),
                }
                if mode == "single"
                else None
            ),
        }
    )
    _autosave()
