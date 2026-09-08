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

### Requirement: Falta de stock KPI uses out_of_stock

When FastAPI is reachable, Explore `Falta de stock` MUST use
`InventoryDashboard.out_of_stock`. Activating the Falta de stock chip MUST send
`out_of_stock=true` on slice and CSV requests. It MUST NOT send
`health_bucket=understock` for that chip.

#### Scenario: Chip filters zero stock

- **GIVEN** Motor listo and the operator activates Falta de stock
- **WHEN** `fetchSlice` / CSV URL are built
- **THEN** the query MUST include `out_of_stock=true`
- **AND** the KPI value MUST equal `dashboard.out_of_stock`

### Requirement: Status chrome hides Catálogo demo while loading live API

When a live API URL is configured and the slice has not failed, product chrome
MUST NOT say `Catálogo demo`. That label is reserved for mock / offline mode.

#### Scenario: First paint with API URL

- **GIVEN** `VITE_SUPPLYMATE_API_URL` is set and the first slice is still loading
- **WHEN** status chrome renders
- **THEN** it MUST NOT display `Catálogo demo`

### Requirement: Seed threads avoid demo catalog names

#### Scenario: Default conversation list

- **GIVEN** a fresh Explore session
- **WHEN** seed thread titles render
- **THEN** they MUST NOT contain Lovable demo category names
  (`Pañales`, `Nutrición`, `Mamaderas`)

### Requirement: CSV export can cover the full recorte

With API up, Export CSV MUST request up to `purchase_skus` rows (capped by the
CSV endpoint max, at least 10_000). The Explore table MAY remain at limit 50.

#### Scenario: Large recorte export

- **GIVEN** `purchase_skus = 5395` and API up
- **WHEN** Exportar orden is clicked
- **THEN** the CSV URL `limit` MUST be `5395` (or the CSV max if lower)
- **AND** MUST NOT be capped at 100
