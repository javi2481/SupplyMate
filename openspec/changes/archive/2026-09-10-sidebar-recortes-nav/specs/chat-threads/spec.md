# Delta for chat-threads

## MODIFIED Requirements

### Requirement: Sidebar chrome

The live sidebar MUST show, in this order: `+ Nuevo recorte`, search input, `Fijados`, `Recientes`. The sidebar primary CTA MUST NOT use the danger/red accent. Thread rail rows MUST NOT use split HTML wrappers around Streamlit buttons. Search MUST filter thread rows case-insensitively using thread title and subtitle. Search MUST treat accent differences as equivalent for matching purposes. Search MUST be local-only and MUST NOT call FastAPI or external services. Empty search input MUST preserve the existing section headings and show the full thread rail. Non-empty search with zero matches MUST show a dedicated no-results message and MUST NOT show misleading empty-section copy such as `Nada fijado` or `Sin recortes recientes`. `ThreadStore.search()` MUST remain presentation-free and MUST NOT own copy, highlighting, or layout rules. The analyst toggle MUST bind to `session_state["analyst_enabled"]` for the current browser session. The analyst toggle MUST NOT be persisted inside thread snapshots. Pin and unpin MUST be available only via a menu on the active thread row (label `···`), not as a permanent full-width button at the foot of the rail. The active row MUST use a subtle highlight (soft fill and left accent), not a strong bordered box as the primary selection cue. Rail titles and subtitles MUST NOT contain the token `SKUs` or the prefix `Catálogo ·`.
(Previously: section heading `Historial de chats`; permanent Fijar/Quitar at rail foot; catalog SKU titles; empty copy `Sin chats recientes`.)

#### Scenario: section order uses Recientes

- GIVEN the sidebar renders with threads present
- WHEN the section headings are inspected
- THEN they MUST appear as `Fijados` then `Recientes`
- AND MUST NOT show `Historial de chats`

#### Scenario: pin via active-row menu

- GIVEN an active unpinned thread
- WHEN the rail first paints
- THEN there MUST NOT be a permanent full-width `Fijar` button at the rail foot
- AND the active row MUST expose a `···` menu containing `Fijar`

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

#### Scenario: rail rows are native not split HTML

- GIVEN one or more persisted threads
- WHEN the thread rail renders
- THEN each row MUST be a Streamlit control without a split HTML wrapper around the button

### Requirement: Title and subtitle

- GIVEN a non-empty scope (not only the default Inventario label)
  WHEN deriving the thread title
  THEN MUST use `compact_scope_line(scope)`
- GIVEN Inventario scope AND catalog/slice SKU count present
  WHEN deriving the title and subtitle
  THEN title MUST be `Inventario general` AND subtitle MUST be `Todos los productos`
  AND title MUST NOT be `Catálogo · {n} SKUs`
- GIVEN Inventario scope AND no catalog count AND at least one non-boilerplate user message
  WHEN deriving the title
  THEN MUST use the first such message, truncated to 48 characters
- GIVEN empty Inventario scope AND no usable user messages
  THEN title MUST be `Nuevo chat` (internal default; visible CTA remains `+ Nuevo recorte`)
- GIVEN a filtered scope AND a non-empty `purchase_list`
  WHEN deriving the subtitle
  THEN MUST be `{n} para reponer` and MUST NOT include the token `SKUs`
- GIVEN a filtered scope AND empty `purchase_list`
  THEN subtitle MUST be empty
- GIVEN two threads sharing the same UTC calendar day AND the same title and subtitle after labeling
  WHEN refreshing labels
  THEN each colliding thread that has a non-boilerplate user question MUST use that question (truncated) as its subtitle

#### Scenario: full inventario uses Inventario general

- GIVEN Inventario scope with `root_skus` or dashboard skus > 0
- WHEN labels are derived
- THEN title MUST be `Inventario general` and subtitle MUST be `Todos los productos`

#### Scenario: filtered subtitle uses para reponer only

- GIVEN a filtered scope with `purchase_list` of length 25
- WHEN labels are derived
- THEN subtitle MUST be `25 para reponer` and MUST NOT contain `SKUs`

### Requirement: Historial grouping

- Unpinned threads MUST list under `Recientes`, newest `updated_at` first, grouped by calendar day labels in UTC: Hoy, Ayer, Esta semana (Monday–Sunday of the current week excluding Hoy and Ayer), then `YYYY-MM-DD`
- Pinned threads MUST appear under `Fijados` and MUST NOT be duplicated in `Recientes`
- Store MUST cap unpinned history at 50 threads (drop oldest unpinned). Pinned threads MUST NOT be dropped by the cap
- Empty Recientes (no unpinned threads) MUST show `Sin recortes recientes`

#### Scenario: Esta semana bucket

- GIVEN an unpinned thread updated earlier this UTC week but not today or yesterday
- WHEN grouping history
- THEN it MUST appear under `Esta semana` and MUST NOT use an ISO date label for that thread

### Requirement: New-thread CTA vs default title

The visible new-thread CTA MUST be `+ Nuevo recorte`. The internal thread title default MUST remain `Nuevo chat`.
