# Delta for chat-threads

## ADDED Requirements

### Requirement: New-thread CTA vs default title

The visible new-thread CTA MUST be `+ Nuevo recorte`. The internal thread title default MAY remain `Nuevo chat`.

#### Scenario: visible CTA and default title differ

- GIVEN an empty new thread with no user messages
- WHEN the rail and thread title are inspected
- THEN the visible new-thread control MUST read `+ Nuevo recorte`
- AND the internal title default MUST remain `Nuevo chat`

## MODIFIED Requirements

### Requirement: Sidebar chrome

The live sidebar MUST show, in this order: `+ Nuevo recorte`, search input, `Fijados`, `Historial de chats`. The sidebar primary CTA MUST NOT use the danger/red accent. Thread rail rows MUST NOT use split HTML wrappers around Streamlit buttons. Search MUST filter thread rows case-insensitively using thread title and subtitle. Search MUST treat accent differences as equivalent for matching purposes. Search MUST be local-only and MUST NOT call FastAPI or external services. Empty search input MUST preserve the existing section headings and show the full thread rail. Non-empty search with zero matches MUST show a dedicated no-results message and MUST NOT show misleading empty-section copy such as `Nada fijado` or `Sin chats recientes`. `ThreadStore.search()` MUST remain presentation-free and MUST NOT own copy, highlighting, or layout rules. The analyst toggle MUST bind to `session_state["analyst_enabled"]` for the current browser session. The analyst toggle MUST NOT be persisted inside thread snapshots.
(Previously: first control labeled `Nuevo chat`; no native-row or non-danger CTA contract.)

#### Scenario: search filters visible thread rows

- GIVEN pinned and historical threads exist in the local store
- WHEN the operator types part of a title or subtitle into the rail search input
- THEN only matching rows MUST remain visible under their respective headings

#### Scenario: empty query shows the full rail

- GIVEN the operator clears the rail search input
- WHEN the sidebar rerenders
- THEN all pinned and historical rows MUST be visible again

#### Scenario: no search matches show dedicated feedback

- GIVEN the operator typed a non-empty query that matches no thread title or subtitle
- WHEN the sidebar rerenders
- THEN the UI MUST show a dedicated no-results message and MUST NOT substitute section empty states

#### Scenario: analyst toggle controls the analyst card

- GIVEN the analyst toggle is off
- WHEN the main panel renders
- THEN the `Lectura del recorte` card MUST be hidden while the rest of the live panel remains visible

#### Scenario: rail rows are native not split HTML

- GIVEN one or more persisted threads
- WHEN the thread rail renders
- THEN each row MUST be a Streamlit control without a split HTML wrapper around the button

#### Scenario: primary CTA is not danger red

- GIVEN the sidebar new-thread control
- WHEN it renders as the primary CTA
- THEN it MUST NOT use the danger/red accent

### Requirement: Nuevo chat

GIVEN the current session has messages or a live list, WHEN the operator clicks `+ Nuevo recorte`, THEN the UI MUST persist the current thread (create or update) AND reset to conversational home (no live panel). GIVEN home with no messages and no live list, WHEN clicking `+ Nuevo recorte`, THEN the UI MUST remain on home without duplicating an empty thread.
(Previously: visible click target was **Nuevo chat**.)

#### Scenario: new thread persists and resets

- GIVEN the current session has messages or a live list
- WHEN the operator clicks `+ Nuevo recorte`
- THEN the UI MUST persist the current thread and reset to conversational home

#### Scenario: empty home does not duplicate

- GIVEN home with no messages and no live list
- WHEN the operator clicks `+ Nuevo recorte`
- THEN the UI MUST remain on home without duplicating an empty thread
