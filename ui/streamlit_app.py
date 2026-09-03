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

from app.models import AnalyticalScope, GuidanceChip, InteractionEvent
from app.services import dashboard as dash_svc
from app.services import metrics, suggested_filters
from app.services import panel_modes
from app.services import scope as scope_svc
from ui import analyst
from ui import charts
from ui import components

metrics = importlib.reload(metrics)
dash_svc = importlib.reload(dash_svc)

API_URL = os.getenv("SUPPLYMATE_API_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_option("client.toolbarMode", "viewer")
st.set_page_config(page_title="SupplyMate", layout="wide", page_icon="📦")
components.inject_theme()
st.markdown("## 📦 SupplyMate · Operación")
st.caption(
    "Explorar (Ask) · Recortá con clicks · Armar OC (Agent) · Exportá · "
    "**Python calcula, el LLM interpreta**"
)

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


def _exit_commit_mode() -> None:
    st.session_state.panel_mode = "explore"
    st.session_state.frozen_scope = None
    _append_event(
        source="mode_transition",
        action="exit_commit",
        label_human="Volver a explorar",
    )
    st.session_state.last_analyze_key = ""


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
    from app.guidance_chips import apply_guidance_chip

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
        return
    scope = scope_svc.clear_highlight(scope)
    st.session_state.highlight_calc = None
    _set_scope(scope)
    st.session_state.last_analyze_key = ""


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
    st.markdown('<div class="sm-panel">', unsafe_allow_html=True)
    panel_mode = st.session_state.panel_mode
    explore_mode = panel_mode == "explore"
    scope = _effective_panel_scope()
    mutable_scope = _scope_model()

    analyst.render_mode_badge(panel_mode)

    slice_data = fetch_slice(scope, limit=25)
    if slice_data is None:
        st.error(f"No pude conectar con la API en `{API_URL}`. Arrancá uvicorn primero.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    st.session_state.slice_data = slice_data
    st.session_state.guidance = slice_data.get("guidance")

    render_breadcrumb(scope, readonly=not explore_mode)
    guidance = st.session_state.guidance or {}
    if explore_mode and guidance.get("action") in ("ask_clarification", "draft_oc"):
        options = guidance.get("options") or []
        chips = guidance.get("chips") or []
        if options:
            if guidance.get("progress_label"):
                step = guidance.get("progress_step") or 0
                total = guidance.get("progress_total") or 0
                st.caption(
                    f"Paso {step} de {total} · {guidance.get('progress_label')}"
                )
            st.markdown(guidance.get("question") or "¿Cómo querés afinar este recorte?")
            guide_cols = st.columns(min(len(options), 4))
            for i, opt in enumerate(options[:6]):
                chip_payload = chips[i] if i < len(chips) else None
                with guide_cols[i % len(guide_cols)]:
                    if st.button(
                        opt,
                        key=f"guide-{scope_svc.cache_key(scope)}-{opt}",
                        type="secondary",
                    ):
                        if chip_payload:
                            apply_guidance_chip_action(chip_payload)
                        else:
                            st.session_state.pending_prompt = opt
                        st.rerun()
                    if chip_payload and chip_payload.get("caption"):
                        st.caption(chip_payload["caption"])
    dash = slice_data.get("dashboard") or {}
    purchase_list = slice_data.get("purchase_list") or []
    evidence = slice_data.get("evidence") or ""
    suggested = slice_data.get("suggested_filters") or []

    analyze_key = _analyze_cache_key(scope, panel_mode)
    if st.session_state.analyst_enabled and analyze_key != st.session_state.last_analyze_key:
        analyze_body = fetch_analyze(_scope_model(), mode=panel_mode)
        if analyze_body:
            st.session_state.analyze_data = analyze_body
            st.session_state.last_analyze_key = analyze_key

    analyze_data = st.session_state.analyze_data or {}
    insight = analyze_data.get("insight")
    commit_summary = analyze_data.get("commit_summary")
    insight_source = analyze_data.get("insight_source", "fallback")

    components.render_kpi_strip(dash, purchase_lines=len(purchase_list))
    components.render_health_legend()
    components.render_coverage_strip(dash.get("coverage") or [])

    analyst.render_analyst_card(
        panel_mode=panel_mode,
        evidence=evidence,
        insight=insight,
        commit_summary=commit_summary,
        insight_source=insight_source,
        analyst_enabled=st.session_state.analyst_enabled,
    )
    analyst.render_exploration_timeline(st.session_state.interaction_events)

    if explore_mode and insight and insight.get("suggested_questions"):
        analyst.render_suggested_questions(
            insight["suggested_questions"],
            key_prefix=f"live-{scope_svc.cache_key(scope)}",
        )

    if explore_mode and suggested:
        st.markdown("**Refinar recorte** — sugerencias determinísticas:")
        chip_cols = st.columns(min(len(suggested), 3))
        for i, chip in enumerate(suggested[:3]):
            if chip_cols[i].button(
                f"➕ {chip['label']}",
                key=f"chip-{scope_svc.cache_key(scope)}-{i}",
                help="Agrega este filtro al breadcrumb",
            ):
                apply_filter_action(chip["action"], chip.get("args") or {}, source="chip")
                st.rerun()

    category_rows = dash.get("by_category") or []
    coverage_rows = dash.get("coverage") or []
    left, right = st.columns(2)
    with left:
        st.markdown(f"**{metrics.LABEL_RECOMMENDED_QTY} por categoría**")
        st.caption("👆 Click en una categoría para recortar" if explore_mode else "Recorte congelado")
        if category_rows:
            cat_chart = charts.lollipop(
                category_rows,
                "category",
                "Categoría",
                extra_tooltips=[alt.Tooltip("sku_count:Q", title="Productos")],
                selectable_field="category" if explore_mode else None,
                selection_name="category_select",
            )
            if explore_mode:
                cat_event = st.altair_chart(
                    cat_chart,
                    on_select="rerun",
                    key="live_category_chart",
                    width="stretch",
                )
                cat_value = charts.selection_value(
                    cat_event, "category", selection_name="category_select"
                )
                if cat_value and cat_value not in mutable_scope.categories:
                    _set_scope(scope_svc.add(mutable_scope, "category", cat_value))
                    _append_event(
                        source="chart_category",
                        action="add_filter",
                        dimension="category",
                        value=cat_value,
                        label_human=cat_value,
                    )
                    st.session_state.last_analyze_key = ""
                    st.rerun()
            else:
                st.altair_chart(cat_chart, width="stretch")
    with right:
        st.markdown(f"**Distribución de {metrics.LABEL_COVERAGE}**")
        st.caption("👆 Click en un bucket para filtrar" if explore_mode else "Recorte congelado")
        if coverage_rows:
            cov_chart = charts.histogram(
                coverage_rows,
                "bucket",
                metrics.LABEL_COVERAGE,
                x_sort=list(dash_svc.COVERAGE_ORDER),
                selectable_field="bucket" if explore_mode else None,
                selection_name="coverage_select",
            )
            if explore_mode:
                cov_event = st.altair_chart(
                    cov_chart,
                    on_select="rerun",
                    key="live_coverage_chart",
                    width="stretch",
                )
                bucket_value = charts.selection_value(
                    cov_event, "bucket", selection_name="coverage_select"
                )
                if bucket_value and bucket_value not in mutable_scope.coverage_buckets:
                    _set_scope(scope_svc.add(mutable_scope, "coverage_bucket", bucket_value))
                    _append_event(
                        source="chart_coverage",
                        action="add_filter",
                        dimension="coverage_bucket",
                        value=bucket_value,
                        label_human=bucket_value,
                    )
                    st.session_state.last_analyze_key = ""
                    st.rerun()
            else:
                st.altair_chart(cov_chart, width="stretch")

    if not purchase_list:
        st.warning("Ningún producto en este recorte. Quitá un filtro o usá **Limpiar filtros**.")
    else:
        components.render_oc_summary(purchase_list)
        st.caption(
            "👆 Click en una fila para ver **Cómo se calculó**"
            if explore_mode
            else "OC congelada — volvé a Explorar para cambiar filtros"
        )
        table_event = components.render_purchase_table(
            purchase_list,
            table_key="live_purchase_table",
            selectable=explore_mode,
        )
        if explore_mode:
            sku = _table_selection_sku(table_event, purchase_list)
            if sku and sku != mutable_scope.highlight_product_id:
                apply_filter_action(
                    suggested_filters.ACTION_OPEN_SKU,
                    {"product_id": sku},
                    source="table_row",
                )
                st.rerun()

    calc_payload = st.session_state.highlight_calc
    if calc_payload and scope.highlight_product_id:
        st.markdown("---")
        st.markdown(f"### 🧮 {calc_payload.get('product_name', scope.highlight_product_id)}")
        cols = st.columns(3)
        cols[0].metric(
            metrics.LABEL_RECOMMENDED_QTY,
            calc_payload.get("recommended_quantity", 0),
            help="Calculado en Python — no lo inventa el LLM",
        )
        ctx = calc_payload.get("context") or {}
        cols[1].metric("Stock actual", ctx.get("current_stock", "—"))
        cols[2].metric(
            metrics.LABEL_REORDER_POINT,
            ctx.get("reorder_point", "—"),
            help=metrics.ROP_CAPTION,
        )
        render_calculation(calc_payload.get("calculation") or {})

    mode_cols = st.columns([2, 2, 2])
    if explore_mode:
        with mode_cols[0]:
            if st.button(
                "Listo — armar OC de este recorte",
                type="primary",
                key="enter_commit",
            ):
                _enter_commit_mode()
                st.rerun()
        with mode_cols[1]:
            st.caption("Export disponible después de congelar el recorte.")
    else:
        with mode_cols[0]:
            csv_bytes = fetch_purchase_csv(scope, limit=max(len(purchase_list), 1))
            if csv_bytes and panel_modes.can_export(panel_mode):
                st.download_button(
                    f"📥 Exportar OC ({len(purchase_list)} SKUs)",
                    data=csv_bytes,
                    file_name="purchase_order.csv",
                    mime="text/csv",
                    key=f"dl-slice-{scope_svc.cache_key(scope)}",
                    type="primary",
                )
        with mode_cols[1]:
            if st.button("Volver a explorar", key="exit_commit"):
                _exit_commit_mode()
                st.rerun()
        with mode_cols[2]:
            if st.session_state.analyst_enabled and st.button("Reconfirmar con IA", key="reanalyze_commit"):
                st.session_state.last_analyze_key = ""
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


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


def render_history() -> None:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("mode") in ("list", "explore"):
                if msg is st.session_state.messages[-1] and st.session_state.live_list_active:
                    pass
                else:
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
            if msg.get("content"):
                st.markdown(msg["content"])


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
        return {"answer": f"Error {response.status_code}: {response.text}", "mode": "error"}

    return response.json()


render_history()

if st.session_state.live_list_active:
    with st.container():
        st.markdown("---")
        st.markdown("### 🎯 Panel de reposición")
        render_live_panel()

with st.sidebar:
    st.markdown("### 📦 SupplyMate")
    st.markdown(
        "1. Preguntá *¿Qué productos tengo que comprar?*  \n"
        "2. Click **Riesgo de quiebre** → categoría → SKU  \n"
        "3. **Armar OC** → exportar CSV  \n"
        "Python calcula qty · LLM interpreta · clicks = 0 LLM"
    )
    st.session_state.analyst_enabled = st.toggle(
        "Analista IA",
        value=st.session_state.analyst_enabled,
    )
    st.divider()
    components.render_health_legend()
    st.divider()
    st.markdown("**SKU demo:** `6033436` → qty **173**")
    if st.button("Limpiar chat", width="stretch"):
        st.session_state.messages = []
        st.session_state.pending_prompt = None
        st.session_state.live_list_active = False
        st.session_state.analytical_scope = scope_svc.reset().model_dump()
        st.session_state.slice_data = None
        st.session_state.highlight_calc = None
        st.session_state.panel_mode = "explore"
        st.session_state.frozen_scope = None
        st.session_state.interaction_events = []
        st.session_state.analyze_data = None
        st.session_state.last_analyze_key = ""
        st.session_state.guidance = None
        st.rerun()

prompt = st.session_state.pending_prompt or st.chat_input(
    "¿Cuánto debería pedir de…?"
)
if st.session_state.pending_prompt:
    st.session_state.pending_prompt = None

if prompt:
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

        if mode in ("list", "explore"):
            interp = data.get("interpretation") or {}
            is_refine = interp.get("relation") == "refinement"
            st.session_state.live_list_active = True
            st.session_state.root_question = prompt
            st.session_state.panel_mode = "explore"
            st.session_state.frozen_scope = None
            if not is_refine:
                st.session_state.interaction_events = []
            st.session_state.analyze_data = None
            st.session_state.last_analyze_key = ""
            st.session_state.guidance = data.get("guidance")
            _append_event(source="chat", action="reset" if not is_refine else "add_filter", label_human=prompt)
            if data.get("scope"):
                _set_scope(AnalyticalScope.model_validate(data["scope"]))
            else:
                _set_scope(scope_svc.reset())
            st.session_state.highlight_calc = None
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

        st.markdown(data.get("answer", ""))

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
