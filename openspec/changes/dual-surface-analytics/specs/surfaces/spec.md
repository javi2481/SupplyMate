# Spec: surfaces

## Purpose

One product in one chat: ask what to buy or what is happening, and see the dashboard in the reply.

## Requirements

### Operation (Streamlit chat)

- The UI MUST be titled SupplyMate (or equivalent branding)
- Streamlit MUST provide chat, inventory dashboard, purchase list table, OC CSV download, and “Cómo se calculó” for single-SKU
- When the user asks what to buy or what is happening, Streamlit MUST render the dashboard **in the chat**: KPI row (SKUs, Stockout Risk, Understock, Overstock, Avg Coverage), at most two charts (lollipop of Recommended Qty by category; histogram of Coverage bins), and the top replenishment table
- Streamlit MUST NOT require a separate Superset (or other BI) app to see this dashboard
- The dashboard MUST NOT include a fabricated demand time-series trend
- Metric labels MUST match the canonical metrics vocabulary

### Shared product identity

- Docs and UI copy MUST present one product with two questions in the same chat:
  “¿Cuánto pedir?” and “¿Qué está pasando?”
- Demo SKU `6033436` SHOULD appear in docs
