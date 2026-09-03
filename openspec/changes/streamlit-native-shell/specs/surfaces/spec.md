# Delta for surfaces

## MODIFIED Requirements

### Requirement: Live panel

ONLY the current list-mode dashboard MUST use interactive charts. Chat history MUST render dashboards without selection. Live Explore MUST render this visual order: compact scope, at most 4 KPIs, two charts (category and coverage). Live Explore MUST NOT restore next-step chips, purchase table, SKU calculation, or analyst as required surfaces. Live panel content MUST NOT be wrapped in split panel HTML. If chips are shown, category and coverage suggested-filter chips MUST NOT duplicate the charts when those charts have data. Live Commit MUST NOT render guidance chips, suggested filters, insight questions, or interactive charts. Live Commit MUST render OC summary, priorities, export, and return-to-explore. KPI density rules apply to the live panel only; the static history dashboard MAY keep its existing KPI row.
(Previously: Explore order required next-step, remaining chips, table, and AI reading; no native-nesting contract.)

#### Scenario: live Explore stays slim

- GIVEN a live Explore dashboard
- WHEN the live panel renders
- THEN the operator MUST see compact scope, at most four KPIs, and two charts
- AND the panel MUST NOT require next-step chips, table, SKU calc, or analyst

#### Scenario: live panel is not split HTML

- GIVEN Explore or Commit live content
- WHEN the live panel renders
- THEN markdown MUST NOT wrap that content in a split panel HTML shell

#### Scenario: commit panel stays non-interactive

- GIVEN panel_mode is commit
- WHEN the live panel renders
- THEN it MUST show OC summary, priorities, export, and return-to-explore
- AND MUST NOT show guidance chips, suggested filters, insight questions, or interactive charts

#### Scenario: only live list charts are interactive

- GIVEN chat history contains a prior dashboard and a live list session is active
- WHEN the app renders
- THEN only the live list dashboard charts MUST be interactive
- AND history dashboards MUST render without selection

### Requirement: Chrome

The main header MUST show compact mode state (Explorando / Revisando compra) and MUST NOT dominate the main pane with product identity. Product name MUST belong in the sidebar. Header MUST NOT teach Ask/Agent/Python/LLM vocabulary. Analyst card title MUST be “Lectura del recorte” with caption “Generado por IA” when that card is shown. Sidebar MUST NOT present non-clickable health ovals as if they were filters. Chat input MUST stay reachable (sticky via `st.bottom` when the input is not at script root).
(Previously: header MUST be product name + tagline + mode in the main pane.)

#### Scenario: compact chrome

- GIVEN a live workspace
- WHEN chrome renders
- THEN the main header MUST show compact mode state and MUST NOT dominate with product identity
- AND the sidebar MUST show the product name
- AND chat input MUST remain reachable via the bottom region

#### Scenario: chrome vocabulary and analyst card

- GIVEN chrome and an analyst card when that card is shown
- WHEN they render
- THEN the header MUST NOT use Ask/Agent/Python/LLM teaching vocabulary
- AND the analyst card title MUST be “Lectura del recorte” with caption “Generado por IA”
- AND the sidebar MUST NOT present non-clickable health ovals as filters
