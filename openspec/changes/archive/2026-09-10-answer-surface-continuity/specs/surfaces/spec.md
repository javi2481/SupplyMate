# Delta for surfaces

## ADDED Requirements

### Requirement: Scope history navigation

Explore MUST maintain a session-only stack of prior `AnalyticalScope` values. Adding a filter (chart, chip, count KPI, highlight, chat refine that changes scope) MUST push the previous scope when its dump differs from the stack top. “Volver” MUST pop and restore that scope, then refresh the live slice. “Limpiar” and new-thread MUST clear the stack and reset to empty scope. History MUST NOT be sent to `/chat` or `/slice` and MUST NOT be fields on `AnalyticalScope`. Stack size MUST be capped (20). Restored history MUST be Pydantic-validated.

#### Scenario: Volver restores previous scope

- GIVEN Explore with Inventario → Cosmética on the stack
- WHEN the operator clicks Volver
- THEN the live scope MUST become Inventario (or prior entry)
- AND the slice MUST refetch for that scope
- AND Limpiar MUST still reset to empty scope in one step

#### Scenario: empty stack disables Volver

- GIVEN no prior scopes on the stack
- WHEN the context bar renders
- THEN Volver MUST be visible and disabled

### Requirement: Count KPIs as controls

Live Explore count KPIs Productos, Falta de stock, and Riesgo de quiebre MUST mutate scope when activated. Cobertura MUST NOT apply a coverage filter from the KPI itself; coverage filtering remains the histogram. Productos MUST clear health, coverage, name tokens, and highlight while keeping categories/subcategories when those extra filters are present.

#### Scenario: Riesgo KPI adds health filter

- GIVEN a live Explore panel with category Cosmética
- WHEN the operator activates Riesgo de quiebre
- THEN `health_buckets` MUST include `stockout_risk`
- AND the slice MUST refresh

### Requirement: SKU answer surface

When `highlight_product_id` is set and calculation data is available, live Explore MUST show a SKU detail card in place of inventory KPIs and charts. The card MUST show operator-facing purchase quantity (“Comprar”), stock, demand, reorder point, and a closed “Cómo se calculó” expander. Chat `mode=single` MUST NOT set `live_list_active` to false. The panel MUST NOT render a second full-text calculation duplicate under the expander.

#### Scenario: single SKU stays in live panel

- GIVEN a live Explore session scoped to Cosmética
- WHEN chat returns mode=single for a product
- THEN live_list_active MUST remain true
- AND the Explore panel MUST show the SKU card with Cosmética still in the context bar
- AND inventory KPI row and category/coverage charts MUST NOT render alongside the SKU card

## MODIFIED Requirements

### Requirement: Live panel

ONLY the current list-mode dashboard MUST use interactive charts. Chat history MUST render dashboards without selection. Live Explore MUST render: context bar when filters, history, or highlight apply; then either (a) at most 4 KPIs and two charts, or (b) SKU detail card when highlight is active. Live Explore MUST NOT restore next-step chips, purchase table, or analyst as required surfaces. Live Commit behavior unchanged.
(Previously: always compact scope + 4 KPIs + two charts; SKU calc forbidden as Explore surface.)

#### Scenario: live Explore stays slim without highlight

- GIVEN a live Explore dashboard without highlight
- WHEN the live panel renders
- THEN the operator MUST see context/scope, at most four KPIs, and two charts
- AND MUST NOT require next-step chips, table, or analyst

#### Scenario: only live list charts are interactive

- GIVEN chat history contains a prior dashboard and a live list session is active
- WHEN the app renders
- THEN only the live list dashboard charts MUST be interactive
- AND history dashboards MUST render without selection
