# Proposal: ui-mockup-polish

## Why

SupplyMate already resolves replenishment decisions in Python and presents them in a Streamlit workspace. The current UI is functionally close to the target operator flow, but it still reads like an internal tool instead of the mockup's conversation-first product surface. Operators should be able to scan the current state, switch between saved recortes, and understand the next action in a few seconds without learning internal architecture terms.

## What Changes

- Add a visual-shell polish layer on top of the existing `ui-v2` and `chat-shell` behavior
- Keep pinned threads from `chat-shell` and add in-memory search in the thread rail
- Promote the header, KPI cards, chart cards, and sticky composer so the app matches the mockup's reading order
- Remove duplicated dashboard rendering between chat history and the live panel
- Keep all replenishment logic, FastAPI contracts, metric formulas, and scope semantics unchanged

## Scope

### In Scope

- Sidebar search for recortes using the existing local thread store
- Sidebar settings toggle for "Lectura con IA"
- Hero-style header and visual polish for live KPI/chart surfaces
- Chat history/live panel unification so the interactive dashboard renders once
- New/updated unit tests and AppTests proving the visual-shell behavior

### Out of Scope

- React, Next.js, Tailwind, custom frontend components, or replacing Streamlit
- Cloud sync, multi-user thread storage, or backend search endpoints
- File upload or real attachment handling in the composer
- Changes to FastAPI, `AnalyticalScope`, guidance ranking, or replenishment formulas

## Capabilities

### New Capabilities

- `visual-shell`: tokens, hero header, chart-card wrappers, styled composer, and chat-bubble polish for the operator-facing Streamlit UI

### Modified Capabilities

- `chat-threads`: searchable thread rail with persistent analyst toggle
- `surfaces`: single live dashboard surface aligned with the current conversation
- `ui-composition`: optional icon metadata for KPI cards and recorte-oriented copy updates

## Dependencies

- Depends on `ui-v2` for Explore/Commit composition and current panel structure
- Depends on `chat-shell` for local thread persistence and sidebar navigation

## Rollback

Revert `openspec/changes/ui-mockup-polish/` and the corresponding `ui/` + `tests/unit/ui/` changes. This leaves `ui-v2` and `chat-shell` intact.
