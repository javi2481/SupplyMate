# Spec: chat-threads

## MODIFIED Requirements

### Sidebar chrome

- The live sidebar MUST show, in this order: `Nuevo chat`, search input, `Fijados`, `Historial de chats`
- Search MUST filter thread rows case-insensitively using thread title and subtitle
- Search MUST treat accent differences as equivalent for matching purposes
- Search MUST be local-only and MUST NOT call FastAPI or external services
- Empty search input MUST preserve the existing section headings and show the full thread rail
- Non-empty search with zero matches MUST show a dedicated no-results message and MUST NOT show misleading empty-section copy such as `Nada fijado` or `Sin chats recientes`
- `ThreadStore.search()` MUST remain presentation-free and MUST NOT own copy, highlighting, or layout rules
- The analyst toggle MUST bind to `session_state["analyst_enabled"]` for the current browser session
- The analyst toggle MUST NOT be persisted inside thread snapshots

#### Scenario: search filters visible thread rows

- **GIVEN** pinned and historical threads exist in the local store
- **WHEN** the operator types part of a title or subtitle into the rail search input
- **THEN** only matching rows MUST remain visible under their respective headings

#### Scenario: empty query shows the full rail

- **GIVEN** the operator clears the rail search input
- **WHEN** the sidebar rerenders
- **THEN** all pinned and historical rows MUST be visible again

#### Scenario: no search matches show dedicated feedback

- **GIVEN** the operator typed a non-empty query that matches no thread title or subtitle
- **WHEN** the sidebar rerenders
- **THEN** the UI MUST show a dedicated no-results message and MUST NOT substitute section empty states

#### Scenario: analyst toggle controls the analyst card

- **GIVEN** the analyst toggle is off
- **WHEN** the main panel renders
- **THEN** the `Lectura del recorte` card MUST be hidden while the rest of the live panel remains visible
