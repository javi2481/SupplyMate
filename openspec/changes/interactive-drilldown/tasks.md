# Tasks: interactive-drilldown

## Phase 0 — SDD

- [x] 0.1 proposal.md, design.md, specs, tasks.md

## Phase 1 — Scope + filter (Strict TDD)

- [x] 1.1 RED/GREEN/TRIANGULATE `AnalyticalScope` add/remove/reset/cache_key
- [x] 1.2 RED/GREEN/TRIANGULATE `filter_rows` OR/AND/highlight
- [x] 1.3 RED/GREEN `chat_dashboard(limit, scope)`

## Phase 2 — Evidence + chips (Strict TDD)

- [x] 2.1 RED/GREEN `format_slice_evidence` + empty state
- [x] 2.2 RED/GREEN `suggest_next_filters` (no LLM)

## Phase 3 — API (Strict TDD)

- [x] 3.1 RED/GREEN `GET /replenishment/slice`
- [x] 3.2 RED/GREEN aligned dashboard/list/csv params

## Phase 4 — Streamlit (verify)

- [x] 4.1 ui/charts.py + live panel, breadcrumb, reset, CSV count
- [x] 4.2 UX checklist procedure in beta-test-protocol (manual run by operator)

## Phase 5 — Ship

- [x] 5.1 README update
- [x] 5.2 verify-report.md; pytest green without live LLM
