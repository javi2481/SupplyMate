# Proposal: interactive-drilldown

## Why

SupplyMate already answers “what should I buy?” with a chat dashboard (KPIs, lollipop, histogram, OC table). The dashboard is static: the user cannot narrow the list before exporting CSV. Today `fetch_purchase_csv` ignores filters, so the exported PO may not match what is on screen.

Users need to **investigate** replenishment (category, coverage, health, supplier) and export **that** slice — without reformulating questions and without the LLM re-interpreting clicks.

## What Changes

- `AnalyticalScope` + deterministic `filter_rows` on cached `_sku_analytics_rows()`
- `GET /replenishment/slice` (scope, evidence, dashboard, purchase_list, suggested_filters)
- Same query params on dashboard, purchase-list, and CSV
- Python `suggest_next_filters` (max 3 chips, no LLM)
- Streamlit: clickable charts, breadcrumb, reset, live panel vs static history
- SKU row = inspection via existing `GET /products/{id}/replenishment`

## Capabilities

- Scope: add (idempotent) / remove / reset; same dimension OR, different AND
- Slice API + aligned CSV export
- Deterministic evidence (“Por qué ves esto”) and empty state
- Suggested filter chips from ranking, not language

## Non-Goals

- `DashboardSpec`, `AnalyticsResponse`, click → utterance → `/chat`
- LLM suggested-questions agent, `explain_agent` on drill-down, `/trace`
- Touch `intents.py` / `classify_intent`
- Checkboxes + Apply, `st.query_params`, scatter, what-if, `ceil()`, embeddings
- Sales mode drill-down; dual-surface doc cleanup

## Roadmap (later changes, not this one)

LLM trace/audit, anti-hallucination validation, horizon what-if, demand×coverage scatter, optional LLM labels on Python-ranked chips.

## Rollback

Remove `openspec/changes/interactive-drilldown/`, revert scope/slice/suggested_filters modules, Streamlit panel wiring, and slice endpoint.

## Risks

- Streamlit `on_select` persists → use `add`, not `toggle`; track last applied selection
- Altair layer charts need `selection_point` spike before wiring both charts
- CSV must use `chat_dashboard(scope)`, not `list_purchase_recommendations` without filter
