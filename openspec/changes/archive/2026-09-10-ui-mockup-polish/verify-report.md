# Verify report: ui-mockup-polish

## pytest

- Focused RED/GREEN commands:
  - `pytest tests/unit/ui/test_composition_kpi_table.py tests/unit/ui/test_visual_shell_apptest.py -q`
  - `pytest tests/unit/ui/test_chat_threads.py tests/unit/ui/test_thread_rail_apptest.py tests/unit/ui/test_visual_shell_apptest.py -q`
  - `pytest tests/unit/ui/test_layout_apptest.py tests/unit/ui/test_visual_shell_apptest.py -q`
  - `pytest tests/unit/ui/test_visual_shell_apptest.py tests/unit/ui/test_layout_apptest.py -q`
- Final suite: `pytest tests/unit/ui/ -m "not llm"`
- Result: `52 passed in 9.92s`

## TDD evidence

| Work unit | RED evidence | GREEN module(s) | Focused result |
|-----------|--------------|-----------------|----------------|
| Foundation | New assertions for `icon_key`, new copy constants, KPI icon markup in `test_composition_kpi_table.py` and `test_visual_shell_apptest.py` failed first | `ui/composition/kpi_policy.py`, `ui/composition/copy.py`, `ui/theme.py`, `ui/components.py` | `5 passed` |
| Sidebar | New search tests in `test_chat_threads.py` and `test_thread_rail_apptest.py` failed first | `ui/threads/store.py`, `ui/threads/rail.py`, `ui/analyst.py` | `24 passed` |
| Main pane | Hero header AppTest failed first; duplicate-live safeguard made explicit in history rendering | `ui/chrome.py`, `ui/streamlit_app.py`, `ui/theme.py` | `7 passed` |
| Visual shell | New chart-card and composer-shell AppTests failed first | `ui/components.py`, `ui/layout_explore.py`, `ui/theme.py`, `ui/streamlit_app.py` | `9 passed` |

## Spec coverage

| Spec | Covered by |
|------|------------|
| `visual-shell` | `tests/unit/ui/test_visual_shell_apptest.py`, `tests/unit/ui/test_composition_kpi_table.py` |
| `chat-threads` | `tests/unit/ui/test_chat_threads.py`, `tests/unit/ui/test_thread_rail_apptest.py`, `tests/unit/ui/test_visual_shell_apptest.py` |
| `surfaces` | `tests/unit/ui/test_layout_apptest.py` |
| `ui-composition` | `tests/unit/ui/test_composition_kpi_table.py`, `tests/unit/ui/test_visual_shell_apptest.py` |

## Runtime harness

- `streamlit run ui/streamlit_app.py --server.headless true --server.port 8501` -> failed because port 8501 was already occupied
- `streamlit run ui/streamlit_app.py --server.headless true --server.port 8502` -> startup succeeded
- HTTP smoke check: `Invoke-WebRequest http://127.0.0.1:8502` -> `200`

## Graphify

- `graphify update .` -> succeeded
- Rebuilt graph: `1702 nodes`, `3424 edges`, `141 communities`

## Lints

- `ReadLints` on `ui/`, `tests/unit/ui/`, and `openspec/changes/ui-mockup-polish/` -> no linter errors found

## Notes

- The visual shell keeps the current Streamlit architecture intact and does not change FastAPI or replenishment behavior.
- Manual visual review in the browser was approximated with a runtime smoke startup plus AppTest coverage, because the verification path in this session is code-first.

## Design review follow-up

Follow-up from [Review ui polish design](1241666b-40c2-4bba-92e6-a5932aee9ed4):

- Documented visual vs behavioral polish boundaries in `design.md`.
- Added explicit UX contracts for search, analyst toggle scope, and single-live-dashboard evidence preservation in specs/design.
- Implemented dedicated no-results search feedback and accent-insensitive matching.
- Added UX resilience matrix and tests for the new contracts.
