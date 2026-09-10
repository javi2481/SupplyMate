# Tasks: ui-v2

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 800–1400 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR1 composition → PR2 explore → PR3 commit |
| Delivery strategy | exception-ok (single tracker, implement sequentially) |
| Chain strategy | feature-branch-chain (optional later) |

## Phase 1: Composition (Strict TDD)

- [x] 1.1 RED/GREEN `compose_next_step` primary/secondary/prompts + stockout dedupe
- [x] 1.2 RED/GREEN KPI policies explore/commit
- [x] 1.3 RED/GREEN table columns + Señal rename
- [x] 1.4 RED/GREEN `chat_would_unfreeze` + compact scope labels
- [x] 1.5 Confirm `test_suggested_filters` and `test_guidance_plan` still green

## Phase 2: Explore layout

- [x] 2.1 Chrome + conversational home
- [x] 2.2 `layout_explore` NextStep / 4 KPIs / compact scope / Lectura del recorte
- [x] 2.3 Honest sidebar (no fake filter ovals)
- [x] 2.4 AppTest.from_function: one NextStep heading, ≤4 explore KPI cards

## Phase 3: Commit + input

- [x] 3.1 `layout_commit` quiet OC surface
- [x] 3.2 Chat confirmation before unfreeze
- [x] 3.3 `st.bottom` chat input + aligned placeholder
- [x] 3.4 Wire `streamlit_app.py`; AppTest commit has no chart keys
- [x] 3.5 `graphify update .`; pytest without live LLM
