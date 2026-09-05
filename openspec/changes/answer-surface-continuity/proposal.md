# Proposal: Answer Surface Continuity

## Why

Category drill-down already narrows the live Explore slice. Three gaps remain: there is no one-step back (only reset-to-root), inventory KPIs look clickable but do nothing, and a concrete SKU answer turns off the live panel and renders as plain metrics + duplicated markdown. Operators lose the Cosmética context and the visual language of the dashboard.

## What Changes

- Session-only `scope_history` stack (push / pop / clear / loads) with cap 20; persisted in thread snapshots
- Explore context bar: ← Volver · compact scope · Limpiar
- Count KPIs become scope controls; Cobertura stays descriptive (histogram remains the coverage control)
- Stronger selected-state on category lollipop (same brand blue)
- Single SKU renders inside the live Explore slot (highlight + calc card); `mode=single` MUST NOT clear `live_list_active`
- One calculation explanation (closed expander); operator copy “Comprar N unidades”
- Histogram value labels; no new charts, no Explore table restore

## Capabilities

- Scope history (session UI state, not AnalyticalScope fields)
- Surfaces: context bar, KPI controls, SKU answer slot
- Visual-shell: selected lollipop contrast; histogram labels; brand-blue intact

## Non-Goals

- FastAPI / slice / chat contract changes; new endpoints
- Restore Explore table, next-step chips, or analyst card
- Recolor coverage bars; browser history / query_params navigation
- Sales mode unification; sidebar / rail changes
- Changing replenishment policy or AnalyticalScope model fields

## Risks

- Streamlit `on_select` persistence → push only when scope dump changes
- KPI look via `st.button` + CSS, not clickable HTML (XSS)
- Old threads without `scope_history` → default `[]`, Volver disabled
