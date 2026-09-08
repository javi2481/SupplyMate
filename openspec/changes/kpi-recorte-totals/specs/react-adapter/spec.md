# Spec: react-adapter (delta)

## ADDED Requirements

### Requirement: Unidades KPI uses dashboard recorte totals

When FastAPI is reachable, Explore `Unidades a pedir` MUST use
`InventoryDashboard.recommended_units` from the current slice. It MUST NOT
sum `purchase_list` / table rows on the happy path.

#### Scenario: Page is smaller than the recorte

- **GIVEN** a live dashboard with `recommended_units = 17753` and a
  `purchase_list` whose qty sum is 6243
- **WHEN** KPIs render
- **THEN** Unidades MUST show 17753
- **AND** the table MAY still show 50 rows

#### Scenario: Offline mock

- **GIVEN** Catálogo demo
- **WHEN** KPIs render
- **THEN** Unidades MAY sum mock rows (the demo catalog is the full recorte)

### Requirement: Table caption names the recorte sample

#### Scenario: Truncated purchase list

- **GIVEN** `purchase_skus >` visible table rows and no table search
- **WHEN** the table chrome renders
- **THEN** the caption MUST state the page size versus `purchase_skus`
  (e.g. `50 de 1.059 a reponer`)
- **AND** MUST NOT imply the table is the full recorte
