"""SupplyMate · Operación — Streamlit assistant (FastAPI /chat + OC export)."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import altair as alt
import httpx
import streamlit as st

from app.services import dashboard as dash_svc
from app.services import metrics

metrics = importlib.reload(metrics)
dash_svc = importlib.reload(dash_svc)

API_URL = os.getenv("SUPPLYMATE_API_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_option("client.toolbarMode", "viewer")
st.set_page_config(page_title="SupplyMate", layout="wide")
st.title("SupplyMate")
st.caption("¿Cuánto pedir? · ¿Qué está pasando? · Horizonte 7 días · Python decide la cantidad")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None
if "last_purchase_csv" not in st.session_state:
    st.session_state.last_purchase_csv = None


def fetch_purchase_csv(limit: int = 25) -> bytes | None:
    try:
        response = httpx.get(
            f"{API_URL}/replenishment/purchase-list.csv",
            params={"limit": limit},
            timeout=120.0,
        )
        if response.status_code == 200:
            return response.content
    except httpx.ConnectError:
        return None
    return None


def _lollipop(
    rows: list[dict],
    y_field: str,
    y_title: str,
    x_field: str = "recommended_quantity",
    x_title: str = "Cantidad recomendada",
    extra_tooltips: list[alt.Tooltip] | None = None,
) -> alt.Chart:
    """Ranking: one categoric + one numeric → lollipop (data-to-viz)."""
    tooltips = [
        alt.Tooltip(f"{y_field}:N", title=y_title),
        *(extra_tooltips or []),
        alt.Tooltip(f"{x_field}:Q", title=x_title),
    ]
    base = alt.Chart(alt.Data(values=rows)).encode(
        x=alt.X(f"{x_field}:Q", title=x_title),
        y=alt.Y(f"{y_field}:N", sort="-x", title=None),
        tooltip=tooltips,
    )
    return (
        base.mark_rule(strokeWidth=2)
        + base.mark_circle(size=90, opacity=1)
    ).properties(height=max(240, 28 * max(len(rows), 1)))


def _histogram(
    rows: list[dict],
    x_field: str,
    x_title: str,
    y_field: str = "sku_count",
    y_title: str = "Productos",
    x_sort: list[str] | None = None,
) -> alt.Chart:
    """Numeric distribution → histogram (ordered bins on X, counts on Y)."""
    return (
        alt.Chart(alt.Data(values=rows))
        .mark_bar(cornerRadiusEnd=2)
        .encode(
            x=alt.X(
                f"{x_field}:N",
                title=x_title,
                sort=x_sort or [],
                axis=alt.Axis(labelAngle=0),
            ),
            y=alt.Y(f"{y_field}:Q", title=y_title),
            tooltip=[
                alt.Tooltip(f"{x_field}:N", title=x_title),
                alt.Tooltip(f"{y_field}:Q", title=y_title),
            ],
        )
        .properties(height=260)
    )


def render_inventory_dashboard(dash: dict | None, purchase_list: list[dict]) -> None:
    dash = dash or {}
    kpis = st.columns(5)
    kpis[0].metric(metrics.LABEL_SKUS, dash.get("skus", "—"))
    kpis[1].metric(metrics.LABEL_STOCKOUT_RISK, dash.get("stockout_risk", "—"))
    kpis[2].metric(metrics.LABEL_UNDERSTOCK, dash.get("understock", "—"))
    kpis[3].metric(metrics.LABEL_OVERSTOCK, dash.get("overstock", "—"))
    avg = dash.get("avg_coverage")
    kpis[4].metric(
        f"{metrics.LABEL_COVERAGE} promedio",
        f"{avg:.1f} d" if isinstance(avg, (int, float)) else "—",
    )

    category_rows = dash.get("by_category") or []
    coverage_rows = dash.get("coverage") or []
    left, right = st.columns(2)
    with left:
        st.caption(f"{metrics.LABEL_RECOMMENDED_QTY} por categoría")
        if category_rows:
            st.altair_chart(
                _lollipop(
                    category_rows,
                    "category",
                    "Categoría",
                    extra_tooltips=[alt.Tooltip("sku_count:Q", title="Productos")],
                ),
                width="stretch",
            )
    with right:
        st.caption(f"Distribución de {metrics.LABEL_COVERAGE}")
        if coverage_rows:
            st.altair_chart(
                _histogram(
                    coverage_rows,
                    "bucket",
                    metrics.LABEL_COVERAGE,
                    x_sort=list(dash_svc.COVERAGE_ORDER),
                ),
                width="stretch",
            )

    total = sum(int(item.get("recommended_quantity") or 0) for item in purchase_list)
    st.markdown(
        f"**{len(purchase_list)} productos para reponer** · "
        f"**{total}** unidades ({metrics.LABEL_RECOMMENDED_QTY})"
    )
    table = [
        {
            "SKU": item.get("product_id", ""),
            "Código de barras": item.get("barcode", ""),
            "Producto": item.get("product_name", ""),
            "Proveedor": item.get("supplier", ""),
            "Categoría": item.get("category", ""),
            "Stock": item.get("current_stock"),
            "Cobertura": item.get("days_of_supply"),
            "Cantidad recomendada": item.get("recommended_quantity"),
            "Estado": metrics.BUCKET_LABELS.get(
                str(item.get("health_bucket") or ""), item.get("health_bucket") or ""
            ),
        }
        for item in purchase_list
    ]
    st.dataframe(table, width="stretch", hide_index=True)


def render_sales_ranking(dash: dict | None) -> None:
    dash = dash or {}
    rows = dash.get("by_sales") or []
    st.caption("Categorías más vendidas (unidades, últimos 30 días)")
    if rows:
        st.altair_chart(
            _lollipop(
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
- Demanda diaria promedio: **{calc.get("average_daily_demand", 0):.2f}**
- Demanda horizonte (7 días): **{calc.get("demand_horizon", 0):.2f}**
- Demanda en lead time: **{calc.get("demand_lead_time", 0):.2f}**
- Stock de seguridad: **{calc.get("safety_stock", 0)}**
- Objetivo de stock: **{calc.get("stock_target", 0):.2f}**
- Stock actual: **{calc.get("current_stock", 0)}**
- **Cantidad recomendada: {calc.get("recommended_quantity", 0)}** (la calcula Python, no el LLM)
"""
        )


def render_history() -> None:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("mode") == "list":
                render_inventory_dashboard(msg.get("dashboard"), msg.get("purchase_list") or [])
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
                    cols[2].metric("Punto de reorden", m.get("rop", "—"))
                if msg.get("calculation"):
                    render_calculation(msg["calculation"])
            if msg.get("content"):
                st.markdown(msg["content"])


def ask_api(prompt: str) -> dict:
    try:
        response = httpx.post(
            f"{API_URL}/chat",
            json={"message": prompt},
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

with st.sidebar:
    st.markdown("### SupplyMate")
    st.markdown(
        "Preguntá **qué comprar**, **qué está pasando** o **cuáles categorías venden más**."
    )
    st.divider()
    st.markdown("Producto puntual: `6033436`")
    if st.button("Limpiar chat", width="stretch"):
        st.session_state.messages = []
        st.session_state.pending_prompt = None
        st.session_state.last_purchase_csv = None
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

        if mode == "list":
            render_inventory_dashboard(dash, purchase_list)
            csv_bytes = fetch_purchase_csv(limit=max(len(purchase_list), 1))
            if csv_bytes:
                st.session_state.last_purchase_csv = csv_bytes
                st.download_button(
                    "Descargar orden de compra (CSV)",
                    data=csv_bytes,
                    file_name="purchase_order.csv",
                    mime="text/csv",
                    key="dl-live",
                )
        elif mode == "sales":
            render_sales_ranking(dash)
        elif mode == "single" and data.get("product_name"):
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
            cols[2].metric("Punto de reorden", ctx.get("reorder_point", "—"))
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
