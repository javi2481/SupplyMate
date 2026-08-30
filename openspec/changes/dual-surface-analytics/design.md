# Design: dual-surface-analytics

> **Superseded (runtime):** DuckDB warehouse and Apache Superset were removed.
> Inventory health is the Streamlit chat dashboard (lollipop + histogram + table).
> Metrics vocabulary in `app/services/metrics.py` still applies.

## Product model

```text
SUPPLYMATE
  ├── Operación (Streamlit) — resolve: how much to order / PO CSV
  └── Analytics (Superset)  — understand: inventory health
         ↑
    DuckDB materialization (Python qty + metrics)
```

UX coherence beats component count. One Superset dashboard only.

## Architecture

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Agent data path | Existing CSV `CatalogStore` | Keep agent tests stable |
| Metrics | `app/services/metrics.py` | Single vocabulary for both surfaces |
| Warehouse | DuckDB file | SQL for Superset without Postgres |
| Qty source | `replenishment.py` only | No SQL formula drift |
| Operation UI | Streamlit | Already the demo assistant |
| Analytics UI | Superset (Compose) | Real BI Explore; not Streamlit charts |

## Anti-patterns avoided

- Health KPI strip inside Streamlit (mini-Superset)
- `/analytics/health` product endpoint for UI
- Demand trend chart without daily series
- Embedding Superset iframe in Streamlit

## Dashboard wire (single)

1. KPIs: SKUs, Stockout Risk, Understock, Overstock, Avg Coverage
2. Charts: by category; coverage distribution
3. Table: top replenishment needs
4. Filters: category / supplier → SKU detail fields aligned with “Cómo se calculó”

## Deep-link

Streamlit sidebar: link to `SUPERSET_URL` (default `http://localhost:8088`).
Docs: “Para pedir → abrir asistente”.
