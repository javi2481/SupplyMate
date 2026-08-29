"""Streamlit chat UI for SupplyMate (calls FastAPI POST /chat)."""

from __future__ import annotations

import os

import httpx
import streamlit as st

API_URL = os.getenv("SUPPLYMATE_API_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(page_title="SupplyMate", page_icon="📦", layout="centered")
st.title("SupplyMate")
st.caption("Asistente de reabastecimiento · horizonte 7 días")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None


def render_history() -> None:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("mode") == "list" and msg.get("purchase_list"):
                st.markdown(f"**{len(msg['purchase_list'])} productos para reponer**")
                for item in msg["purchase_list"]:
                    st.markdown(
                        f"- **{item['product_name']}** — pedir **{item['recommended_quantity']}** u."
                    )
            else:
                if msg.get("product_name"):
                    st.markdown(f"**{msg['product_name']}**")
                if msg.get("quantity") is not None:
                    st.metric("Cantidad recomendada", msg["quantity"])
                if msg.get("metrics"):
                    cols = st.columns(3)
                    m = msg["metrics"]
                    cols[0].metric("Stock actual", m.get("stock", "—"))
                    cols[1].metric("Ventas/día", m.get("avg_daily", "—"))
                    cols[2].metric("Punto de quiebre", m.get("rop", "—"))
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
    st.markdown(
        "Preguntá por un producto o pedí la lista: "
        "*¿Qué productos tengo que comprar?*"
    )
    if st.button("Limpiar chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_prompt = None
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

        if mode == "list" and purchase_list:
            st.markdown(f"**{len(purchase_list)} productos para reponer**")
            for item in purchase_list:
                st.markdown(
                    f"- **{item['product_name']}** — pedir **{item['recommended_quantity']}** u."
                )
        elif mode == "single" and data.get("product_name"):
            ctx = data.get("context") or {}
            calc = data.get("calculation") or {}
            st.markdown(f"**{data['product_name']}**")
            st.metric("Cantidad recomendada", data.get("recommended_quantity", 0))
            cols = st.columns(3)
            cols[0].metric("Stock actual", ctx.get("current_stock", "—"))
            cols[1].metric("Ventas/día", round(calc.get("average_daily_demand", 0), 1))
            cols[2].metric("Punto de quiebre", ctx.get("reorder_point", "—"))

        st.markdown(data.get("answer", ""))

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": data.get("answer", ""),
            "mode": data.get("mode"),
            "product_name": data.get("product_name"),
            "quantity": data.get("recommended_quantity"),
            "purchase_list": data.get("purchase_list") or [],
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
