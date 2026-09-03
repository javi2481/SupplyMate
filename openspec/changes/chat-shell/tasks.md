# Tasks: chat-shell

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 400–700 |
| 400-line budget risk | Medium |
| Chained PRs recommended | No (single change, sequential TDD) |
| Delivery strategy | exception-ok |
| Depends on | ui-v2 (Explore/Commit composition already in tree) |

## Phase 1: Thread store (Strict TDD, no Streamlit)

- [x] 1.1 RED/GREEN `Thread` snapshot round-trip (include listed fields, exclude CSV bytes)
- [x] 1.2 RED/GREEN `title_for_thread` via `compact_scope_line` + first-message fallback + “Nuevo chat”
- [x] 1.3 RED/GREEN pin/unpin; pinned excluded from history list
- [x] 1.4 RED/GREEN `group_history_by_day` (Hoy / Ayer / `YYYY-MM-DD`)
- [x] 1.5 RED/GREEN persist/load JSON; corrupt file → empty index; cap 50 unpinned
- [x] 1.6 RED/GREEN `new_chat_should_persist` (dirty vs empty home)

## Phase 2: Sidebar chrome (AppTest)

- [x] 2.1 RED/GREEN sidebar order: Nuevo chat, Fijados, Historial de chats
- [x] 2.2 RED/GREEN empty Fijados caption; no Limpiar chat as first-class sidebar action
- [x] 2.3 RED/GREEN selecting a history row restores messages + scope into the harness state

## Phase 3: Wire orchestrator

- [x] 3.1 Autosave after chat/scope mutation; restore before layout render
- [x] 3.2 Nuevo chat → persist dirty session → conversational home
- [x] 3.3 Restored commit thread keeps `frozen_scope`; `chat_would_unfreeze` still applies
- [x] 3.4 Confirm ui-v2 composition/layout tests still green
- [x] 3.5 `graphify update .`; pytest without live LLM
