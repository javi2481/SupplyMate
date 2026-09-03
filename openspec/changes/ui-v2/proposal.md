# Proposal: ui-v2

## Why

SupplyMate already decides replenishment in Python and explains with an LLM. The Streamlit UI still presents chat, guidance, suggested filters, insight questions, KPIs, charts, table, and “Analista IA” as simultaneous first-class surfaces. Operators cannot answer “what am I doing now?” in two seconds.

## What Changes

- Presentation-only composition: one “Siguiente paso” over existing `guidance`, `suggested_filters`, and insight `suggested_questions`
- Conversation-first Explore layout; quiet Commit layout
- Compact chrome, 4 live KPIs, job-first table columns, sticky chat via `st.bottom`
- Commit chat MUST NOT silently clear `frozen_scope`
- Rename table “Tendencia” to “Señal” (no time series)

## Capabilities

- New: `ui-composition` (NextStep, KPI policy, table policy, copy, chat-unfreeze policy)
- Modified: `surfaces` (hierarchy, home, commit silence, sticky input, honest sidebar)
- Modified: `suggested-filters` (ranking unchanged; UI shows chips as secondary when guidance is primary)

## Non-Goals

- FastAPI / Pydantic / `AnalyticalScope` / guidance engine / `suggest_next_filters` ranking
- React, Figma, `st.navigation` pages, Playwright e2e, new metrics or formulas
- Merging the two chip engines into one domain service

## Rollback

Delete `openspec/changes/ui-v2/` and revert `ui/` composition/layout files plus `streamlit_app.py` wiring.
