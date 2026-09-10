# Design: ui-v2

## Principle

**Compose in the UI. Do not change slice JSON or chip engines.**

`GET /replenishment/slice` already returns `guidance` + `suggested_filters`. Analyze already returns insight questions. `compose_next_step` is a Streamlit-free helper under `ui/composition/`.

```text
slice.guidance ─┐
slice.suggested_filters ─┼─ compose_next_step → NextStep
insight.suggested_questions ─┘
        │
        ├─ layout_explore (rich)
        └─ layout_commit (quiet)
```

## Apply adapters (unchanged)

- Guidance chips → `apply_guidance_chip_action` (`draft_oc` still calls `_enter_commit_mode`)
- Suggested filters → `apply_filter_action` (`open_sku` still sets highlight)
- Chart `on_select` → `add` only

## Commit + chat

Today a list/explore `/chat` turn sets `panel_mode="explore"` and `frozen_scope=None`. ui-v2 stores a `pending_unfreeze` payload and asks confirmation before that reset. Analyze/CSV keep sending `frozen_scope`.

## Live vs history KPIs

`explore_kpi_keys` applies to `render_live_panel` only. `render_inventory_dashboard_static` keeps the dual-surface history strip.

## Files

- `ui/composition/*` — NextStep, KPIs, columns, copy, unfreeze policy
- `ui/layout_explore.py`, `ui/layout_commit.py`, `ui/chrome.py`
- `ui/streamlit_app.py` — thinner orchestrator
- Tests: `tests/unit/ui/test_composition_*.py`, AppTest harnesses for layout

## Threat matrix

N/A — no new routing, subprocess, or auth boundary. HTML/CSS remains existing `unsafe_allow_html` theme cards.
