# Design: ui-mockup-polish

## Technical Approach

Implement a presentation-focused change on top of `ui-v2` and `chat-shell`. The design keeps the current FastAPI, scoping, and replenishment logic untouched, and concentrates mockup alignment inside Streamlit presentation modules, Streamlit-free composition helpers, and focused AppTests.

This change mixes two layers:

- **Visual polish**: tokens, hero header, KPI/chart cards, composer shell, chat-bubble styling.
- **Behavioral polish**: sidebar search, analyst toggle wiring, and single-live-dashboard history rules.

## UX Contracts

### Search

- Fields: `Thread.title` and `Thread.subtitle` only.
- Matching: substring, case-insensitive, accent-insensitive.
- Empty query: show full rail with existing section headings.
- Zero matches: show `Sin recortes que coincidan`; do not show misleading section empty states.
- Ordering: preserve existing pinned/history order; filtering happens in the rail, not in the store.

### Analyst toggle

- Binds to `session_state["analyst_enabled"]`.
- Scope: current browser session only; not stored in thread snapshots.
- Effect: hides the `Lectura del recorte` card when off; live KPIs, charts, and table remain visible.

### Single live dashboard

- When `live_list_active` is true, assistant explore/list history turns MUST NOT render static dashboards.
- Older turns keep their text content; only the latest active turn MAY show the compact summary bar.
- The only interactive dashboard surface is `render_live_panel()`.

### Theme boundaries

- `ui/theme.py` owns tokens and shell CSS only.
- `ui/components.py`, `ui/chrome.py`, and `ui/threads/rail.py` own layout/render decisions.
- `ui/threads/store.py` stays presentation-free.

## Architecture Decisions

### Decision: Keep Streamlit as the rendering platform

**Choice**: Use Streamlit + CSS/HTML polish instead of replacing the UI stack.  
**Alternatives considered**: React/Next.js, custom Streamlit components.  
**Rationale**: The current app already has the full operator workflow. Replatforming would expand scope far beyond the mockup gap.

### Decision: Search belongs in the thread store

**Choice**: Add a local `ThreadStore.search()` helper and let the rail render filtered results.  
**Alternatives considered**: Search logic inside `rail.py`, backend or full-text indexing.  
**Rationale**: Search is local-only, easy to unit test, and should stay Streamlit-free.

### Decision: Render one live dashboard only

**Choice**: Keep the active dashboard in `render_live_panel()` and suppress duplicate static dashboard rendering from earlier active-thread history turns.  
**Alternatives considered**: Preserve both static history dashboards and the live dashboard.  
**Rationale**: The mockup emphasizes one current workspace, reduces scroll, and avoids repeated evidence blocks.

### Decision: Add icon metadata, not icon logic, to KPI composition

**Choice**: Extend `KpiCard` with optional icon metadata and keep rendering choices in the presentation layer.  
**Alternatives considered**: Hardcode icons in `components.py` without composition support.  
**Rationale**: Composition remains testable, while rendering can evolve independently.

## Data Flow

```text
sidebar search input
      |
      v
ThreadStore.search(query)
      |
      v
filtered pinned/history threads
      |
      v
render_thread_rail()
      |
      +--> switch_thread() -> session_state restore
      |
      +--> analyst toggle -> session_state["analyst_enabled"]

session_state
      |
      v
streamlit_app.py
      |
      +--> render_history()      (text-only for older live turns)
      +--> render_live_panel()   (single interactive dashboard)
      +--> chrome.render_header()
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `openspec/changes/ui-mockup-polish/state.yaml` | Create | Track strict TDD phase status and dependencies. |
| `openspec/changes/ui-mockup-polish/proposal.md` | Create | Record intent, scope, and non-goals for the mockup polish change. |
| `openspec/changes/ui-mockup-polish/specs/visual-shell/spec.md` | Create | Define the new visual shell capability. |
| `openspec/changes/ui-mockup-polish/specs/chat-threads/spec.md` | Create | Define searchable rail and analyst toggle behavior. |
| `openspec/changes/ui-mockup-polish/specs/surfaces/spec.md` | Create | Define single-live-dashboard behavior. |
| `openspec/changes/ui-mockup-polish/specs/ui-composition/spec.md` | Create | Define optional KPI icon metadata and copy updates. |
| `ui/theme.py` | Modify | Centralize tokens and add visual shell CSS classes. |
| `ui/composition/copy.py` | Modify | Add copy for search and analyst toggle; adjust visible labels if needed. |
| `ui/composition/kpi_policy.py` | Modify | Add optional icon metadata to live KPI cards. |
| `ui/components.py` | Modify | Render icon-aware KPI cards and reusable chart cards. |
| `ui/chrome.py` | Modify | Replace compact header with hero-style shell header. |
| `ui/threads/store.py` | Modify | Add search helper for title/subtitle filtering. |
| `ui/threads/rail.py` | Modify | Add search input and analyst toggle wiring. |
| `ui/layout_explore.py` | Modify | Wrap charts in reusable chart-card containers. |
| `ui/streamlit_app.py` | Modify | Suppress duplicate history dashboards and wire sidebar state. |
| `tests/unit/ui/test_thread_search.py` | Create | Unit tests for thread search behavior. |
| `tests/unit/ui/test_visual_shell_apptest.py` | Create | AppTests for header, search, toggle, and shell wrappers. |
| `tests/unit/ui/test_layout_apptest.py` | Modify | Ensure the active thread renders a single live dashboard. |

## Testing Strategy

- Strict TDD is active from `openspec/config.yaml`
- Add a RED test before every production change
- Keep unit tests for Streamlit-free helpers small and deterministic
- Use AppTest for sidebar/header/layout behavior without hitting FastAPI
- Run focused tests per work unit, then `pytest tests/unit/ui/ -m "not llm"` as the wider regression proof

## Threat Matrix

Security threat matrix: not applicable. This change does not alter routing, auth, subprocesses, VCS automation, or external integrations.

### UX resilience matrix

| Failure mode | Expected behavior | Covered by |
|--------------|-------------------|------------|
| Search query matches nothing | Dedicated no-results copy, no misleading section empties | `test_thread_rail_apptest.py` |
| Accent/case mismatch in search | Accent-insensitive substring match | `test_chat_threads.py` |
| Analyst toggle off | Analyst card hidden, live evidence remains | `test_visual_shell_apptest.py` |
| Live thread with prior explore turns | Text preserved, no duplicate static dashboards | `test_layout_apptest.py` |
| Streamlit CSS drift | AppTest checks for shell class markers | `test_visual_shell_apptest.py` |
