# Design: chat-shell

## Principle

**ChatGPT chrome around SupplyMate work, not a chat product.**

The left rail is navigation (threads). The center is the operational workspace from ui-v2. Persistence is a local thread index; engines stay untouched.

```text
  sidebar (Nuevo / Fijados / Historial)
           │
           ▼
  ThreadStore (JSON) ── snapshot ── session_state
           │
           ▼
  layout_explore | layout_commit | conversational home
```

## Architecture

- `ui/threads/` is Streamlit-free: dataclasses, title, pin, cap, day grouping, load/save
- `ui/chrome.py` (or a thin `ui/threads/sidebar.py`) renders the rail and returns the selected action
- `ui/streamlit_app.py` remains the orchestrator: autosave on mutation, restore on click, reset on Nuevo chat
- Path to JSON is injectable (`ThreadStore(path=...)`) so tests never touch the operator’s file
- Default path: `Path.home() / ".supplymate" / "threads.json"` (survives git clean; not committed)

## Snapshot vs session_state

Copy only the fields in the chat-threads spec. Do **not** persist `csv_bytes`. On restore of a commit thread, OC CSV is regenerated the same way ui-v2 already does when the operator is in commit.

Autosave after: chat response applied, filter/chip/chart apply, pin toggle, panel mode change. Not on every Streamlit widget tick.

## UX

- Labels stay Spanish product copy: **Nuevo chat**, **Fijados**, **Historial de chats**
- Thread title = compact scope (`Pañales · Bebé · XXG`), never ten copies of the buy question
- **Limpiar** inside Explore still clears **scope in this thread**; it does not delete the thread
- **Nuevo chat** is the ChatGPT “new conversation” action (replaces sidebar Limpiar chat)
- Empty Fijados: heading + “Nada fijado”, no placeholder threads
- Analyst expander stays at the bottom of the sidebar (settings, not a fourth nav group)

## TDD boundary

Phase 1 tests import `ui.threads` only. Phase 2 AppTest asserts sidebar widgets and restore without hitting FastAPI. Phase 3 wires `streamlit_app.py` and keeps ui-v2 layout tests green.

## Non-goals (enforced)

No FastAPI chat resource, no React, no `st.navigation` multi-page app, no backend contract changes.
