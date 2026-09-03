# Proposal: chat-shell

## Why

Operators lose the current recorte when they hit “Limpiar chat” or refresh. They asked for ChatGPT chrome so they can pin recurring work and resume yesterday’s cut. The replenishment engines are fine; the missing product is a thread of (conversation + scope), not a new metric.

## What Changes

- Sidebar becomes ChatGPT-shaped navigation: **Nuevo chat**, **Fijados**, **Historial de chats**
- The main pane stays the ui-v2 SupplyMate workspace (home / Explore / Commit)
- Each thread snapshot restores messages **and** operational state (`AnalyticalScope`, panel mode, frozen scope, live slice)
- Thread titles come from `compact_scope_line`, not the generic first question
- Persistence is local JSON (same machine, survives F5). No FastAPI chat API

## Capabilities

- New: `chat-threads` (thread model, pin, snapshot/restore, title, day grouping)
- Modified: `surfaces` (sidebar chrome; Nuevo chat replaces Limpiar chat as the empty-home action)

## Non-Goals

- FastAPI / Pydantic contracts, guidance engine, `suggest_next_filters`, slice JSON
- React, `st.navigation` pages, multi-user accounts, cloud sync, search, folders
- Changing Explore/Commit composition from ui-v2
- Storing CSV bytes in the snapshot (regenerate on Commit)

## Rollback

Delete `openspec/changes/chat-shell/` and revert `ui/threads/`, sidebar wiring in `ui/streamlit_app.py` / `ui/chrome.py`.
