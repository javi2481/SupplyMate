# Tasks: ui-mockup-polish

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 700-1100 |
| 400-line budget risk | Medium |
| Chained PRs recommended | Yes |
| Suggested split | PR1 foundation -> PR2 sidebar -> PR3 main pane -> PR4 visual shell |
| Delivery strategy | feature-branch-chain |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Theme tokens, copy, KPI icon metadata | PR 1 | `pytest tests/unit/ui/test_composition_kpi_table.py -q` | N/A - presentation metadata only | `ui/theme.py`, `ui/composition/copy.py`, `ui/composition/kpi_policy.py`, related tests |
| 2 | Sidebar search and analyst toggle | PR 2 | `pytest tests/unit/ui/test_chat_threads.py tests/unit/ui/test_thread_rail_apptest.py tests/unit/ui/test_visual_shell_apptest.py -q` | AppTest sidebar harness | `ui/threads/*`, sidebar wiring, related tests |
| 3 | Hero header and single live dashboard | PR 3 | `pytest tests/unit/ui/test_layout_apptest.py tests/unit/ui/test_visual_shell_apptest.py -q` | AppTest main-pane harness | `ui/chrome.py`, `ui/streamlit_app.py`, related tests |
| 4 | Chart cards, composer shell, final polish | PR 4 | `pytest tests/unit/ui/test_visual_shell_apptest.py tests/unit/ui/test_layout_apptest.py -q` | AppTest visual shell harness | `ui/components.py`, `ui/layout_explore.py`, `ui/theme.py`, related tests |

## Phase 1: OpenSpec artifacts

- [x] 1.1 Create `openspec/changes/ui-mockup-polish/state.yaml` with strict TDD and dependencies
- [x] 1.2 Create `proposal.md` with intent, scope, and non-goals
- [x] 1.3 Create spec deltas for `visual-shell`, `chat-threads`, `surfaces`, and `ui-composition`
- [x] 1.4 Create `design.md` with architecture decisions, file map, and testing strategy
- [x] 1.5 Create `tasks.md` with chained work units and focused test commands

## Phase 2: PR1 Foundation (Strict TDD)

- [x] 2.1 RED/GREEN optional KPI icon metadata in `ui/composition/kpi_policy.py`
- [x] 2.2 RED/GREEN shell copy additions in `ui/composition/copy.py`
- [x] 2.3 RED/GREEN central visual tokens and KPI icon rendering in `ui/theme.py` and `ui/components.py`

## Phase 3: PR2 Sidebar (Strict TDD)

- [x] 3.1 RED/GREEN `ThreadStore.search()` title/subtitle filtering
- [x] 3.2 RED/GREEN sidebar search input and filtered rendering in `ui/threads/rail.py`
- [x] 3.3 RED/GREEN analyst toggle wiring between sidebar and live panel

## Phase 4: PR3 Main pane (Strict TDD)

- [x] 4.1 RED/GREEN hero header in `ui/chrome.py`
- [x] 4.2 RED/GREEN suppress duplicate active-thread dashboards in `ui/streamlit_app.py`
- [x] 4.3 RED/GREEN preserve summary bar and active conversation order

## Phase 5: PR4 Visual shell (Strict TDD)

- [x] 5.1 RED/GREEN reusable chart-card wrapper in `ui/components.py`
- [x] 5.2 RED/GREEN chart-card integration in `ui/layout_explore.py`
- [x] 5.3 RED/GREEN sticky composer and chat-bubble polish in `ui/theme.py` and `ui/streamlit_app.py`

## Phase 6: Verify

- [x] 6.1 Run focused tests per work unit and keep TDD evidence
- [x] 6.2 Run `pytest tests/unit/ui/ -m "not llm"` and confirm green
- [x] 6.3 Run `graphify update .`
- [x] 6.4 Write `verify-report.md` with RED/GREEN mapping and final results
