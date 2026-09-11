# Delta for react-adapter

Panel-surface continuity. The rules below key on the **payload shape** of
`ChatResponse` (which of `scope` and `dashboard` are present), not on a list of
mode names, so a new mode inherits the correct behavior without a UI branch.

## ADDED Requirements

### Requirement: The response payload decides the panel surface

`applyChatScope` MUST project the panel from the response payload shape:

1. `scope` present — the response owns a recorte; the adapter MUST map it onto
   the live slice as today.
2. `scope` absent and `dashboard` present — the response carries its own
   surface; the adapter MUST replace the live panel with that surface and MUST
   NOT leave the previous recorte's KPIs, charts, or context bar on screen.
3. `scope` absent and `dashboard` absent — the turn is conversational; the
   adapter MUST leave the panel untouched.

The adapter MUST NOT parse the answer text to decide which branch applies, and
MUST NOT special-case a mode string to obtain the correct surface.

#### Scenario: Sales turn replaces the replenishment panel

- **GIVEN** Explore shows replenishment KPIs and charts for the previous recorte
- **WHEN** a chat turn returns `mode = "sales"` with a `dashboard` and no
  `scope`
- **THEN** the panel MUST render the surface carried by that response
- **AND** the previous recorte's replenishment KPIs and chart MUST NOT remain
  visible
- **AND** the context bar MUST NOT keep advertising the previous filters

#### Scenario: Conversational turn leaves the panel alone

- **GIVEN** Explore shows a recorte
- **WHEN** a chat turn returns neither `scope` nor `dashboard` (for example a
  disambiguation question)
- **THEN** the live slice MUST be unchanged
- **AND** the panel MUST keep rendering the current recorte

#### Scenario: Scoped turn still maps the recorte

- **GIVEN** any prior panel state
- **WHEN** a chat turn returns a `scope`
- **THEN** the live slice MUST be derived from that scope
- **AND** the returned scope MUST win over the previous UI state

### Requirement: A replaced surface renders only what the turn computed

When the panel surface is replaced under rule 2 above, every number on screen
MUST come from that response's `dashboard`. The panel MUST NOT render purchase
counters (units to order, SKUs to replenish, estimated purchase value) that
belong to a recorte the turn did not compute, and MUST NOT offer purchase
actions (export CSV of the recorte, build the order) derived from the stale
slice.

#### Scenario: No stale purchase counters under a replaced surface

- **GIVEN** a replaced panel surface from a `scope`-less response
- **WHEN** the panel renders
- **THEN** every KPI and chart value MUST come from `res.dashboard`
- **AND** replenishment KPIs from the prior slice MUST NOT render
- **AND** recorte purchase actions MUST NOT be offered for the prior slice

### Requirement: Surface replacement is local to the panel

The replacement MUST be a client-side projection only. The adapter MUST NOT
send the reset as a scope mutation to `/chat` or `/slice`, and MUST NOT treat it
as a user filter change for history purposes in a way that prevents the server
from restoring conversational continuity. When the next response carries a
`scope`, that scope MUST be applied even if it re-establishes the recorte that
was on screen before the replacement.

#### Scenario: Follow-up after a replacement restores the recorte

- **GIVEN** a recorte on screen, then a `scope`-less turn that replaced the
  panel
- **WHEN** the next turn returns a `scope` that refines the original recorte
- **THEN** the panel MUST render that returned scope
- **AND** the adapter MUST NOT have sent the intermediate reset to the server as
  a filter change

## MODIFIED Requirements

### Requirement: Unidades KPI uses dashboard recorte totals

When FastAPI is reachable and the panel is showing a recorte, Explore
`Unidades a pedir` MUST use `InventoryDashboard.recommended_units` from the
current slice. It MUST NOT sum `purchase_list` / table rows on the happy path.
When the panel surface has been replaced by a `scope`-less response, the
purchase KPI row MUST NOT render at all rather than showing the previous
recorte's totals.
(Previously: the KPI always rendered from the current slice, with no rule for a
replaced surface.)

#### Scenario: Page is smaller than the recorte

- **GIVEN** a live dashboard with `recommended_units = 17753` and a
  `purchase_list` whose qty sum is 6243
- **WHEN** KPIs render
- **THEN** Unidades MUST show 17753
- **AND** the table MAY still show 50 rows

#### Scenario: Replaced surface hides the purchase KPI row

- **GIVEN** a `scope`-less response that replaced the panel surface
- **WHEN** the panel renders
- **THEN** the purchase KPI row MUST NOT render
- **AND** the stale `recommended_units` value MUST NOT appear anywhere

#### Scenario: Offline mock

- **GIVEN** Catálogo demo
- **WHEN** KPIs render
- **THEN** Unidades MAY sum mock rows (the demo catalog is the full recorte)
