# Tasks: Sidebar Recortes Nav

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 250–400 |
| 400-line budget risk | Low–Medium |
| Chained PRs recommended | No |
| Delivery strategy | single-PR |

## Phase 1: Spec + copy

- [x] 1.1 OpenSpec change `sidebar-recortes-nav` (proposal, design, specs, tasks, state)
- [x] 1.2 `ui/composition/copy.py`: `HISTORY_SECTION = "Recientes"`; `HISTORY_EMPTY = "Sin recortes recientes"`; `THREAD_MENU = "···"`

## Phase 2: Labels + groups (TDD)

- [x] 2.1 RED rewrite title/subtitle/group/search/clone tests in `tests/unit/ui/test_chat_threads.py`
- [x] 2.2 GREEN `title_for_thread` / `_subtitle_from_snap` / clone disambiguation in `ui/threads/store.py`
- [x] 2.3 GREEN `group_history_by_day` Hoy / Ayer / Esta semana / ISO

## Phase 3: Rail chrome (TDD)

- [x] 3.1 RED AppTests: Recientes, no permanent Fijar, `···` when active, no rail-row wrappers
- [x] 3.2 GREEN `ui/threads/rail.py` popover on active row; remove foot pin buttons
- [x] 3.3 GREEN `ui/theme.py` active-container restyle

## Phase 4: Verify

- [x] 4.1 `pytest tests/unit/ui/test_chat_threads.py tests/unit/ui/test_thread_rail_apptest.py tests/unit/ui/test_visual_shell_apptest.py -m "not llm"`
- [x] 4.2 Browser sidebar on :8501 — Inventario general, Recientes, no Catálogo·SKUs
- [x] 4.3 `graphify update .`
