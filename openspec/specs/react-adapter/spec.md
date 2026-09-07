# Spec: react-adapter

## Requirements

### Requirement: Visual projection without domain math

Given a `PurchaseListItem` from FastAPI, the adapter MUST produce a visual row
for the ops table without inventing replenishment intermediates
(`demand_horizon`, `demand_lead`, `stock_target`, `lead_time_days`,
`safety_stock`). Those fields MAY only appear after
`GET /products/{id}/replenishment`.

#### Scenario: Table row from purchase list

- **GIVEN** a `PurchaseListItem` with `recommended_quantity`, `current_stock`,
  `days_of_supply`, `operational_priority`, `health_bucket`
- **WHEN** the adapter maps it to a list row
- **THEN** qty, stock, coverage, and priority label MUST come from the item
- **AND** demand/lead/safety fields MUST be absent or null until SKU detail loads

### Requirement: Priority labels match backend

#### Scenario: Critical vs high

- **GIVEN** `operational_priority` values `critical`, `high`, `normal`
- **WHEN** labels are rendered
- **THEN** they MUST be `Crítica`, `Alta`, `Normal` respectively
- **AND** MUST NOT map both `critical` and `high` to the same label

### Requirement: Health labels match backend

#### Scenario: Understock copy

- **GIVEN** `health_bucket === "understock"`
- **WHEN** the health chip is shown
- **THEN** the label MUST be `Falta de stock`

### Requirement: KPI clicks do not compute qty

#### Scenario: Filter only

- **GIVEN** the operator clicks a KPI (e.g. stockout risk)
- **WHEN** the slice updates
- **THEN** recommended quantities MUST still come from the API (or mock catalog in offline mode)
- **AND** the UI MUST NOT recompute order-up-to in TypeScript on the happy path

### Requirement: SKU drawer uses replenishment endpoint

#### Scenario: Open SKU detail with API up

- **GIVEN** FastAPI is reachable
- **WHEN** the operator opens a SKU drawer
- **THEN** calculation facts MUST load from `GET /products/{id}/replenishment`

### Requirement: CSV export uses the same scope

#### Scenario: Export PO

- **GIVEN** an active AnalyticalScope (categories, coverage, health, …)
- **WHEN** Export CSV is clicked with API up
- **THEN** the download URL MUST use the same query params as the current slice

### Requirement: Offline fallback hides API URL

#### Scenario: API down

- **GIVEN** the slice fetch fails
- **WHEN** the UI shows the demo catalog
- **THEN** product chrome MUST say `Catálogo demo` (or equivalent)
- **AND** MUST NOT display localhost / API host strings

### Requirement: Coverage chips match COVERAGE_ORDER

Explore coverage chips MUST be the five canonical `COVERAGE_ORDER` labels
(`0–3 días`, `3–7 días`, `7–14 días`, `14–30 días`, `30+ días`) with Unicode
en-dash. The UI MUST NOT render a `14+` chip that spans two backend bands.

#### Scenario: Five chips, canonical labels

- **GIVEN** the Explore filter row
- **WHEN** coverage chips render
- **THEN** there MUST be exactly five chips whose labels are `COVERAGE_ORDER`
- **AND** MUST NOT render a `14+` chip

#### Scenario: One chip, one bucket

- **GIVEN** the operator selects `14–30 días`
- **WHEN** `sliceToScopeQuery` / `fetchSlice` / CSV URL are built
- **THEN** `coverage_bucket` MUST be exactly `["14–30 días"]`
- **AND** MUST NOT also include `30+ días`

#### Scenario: Mock fallback uses the same edges

- **GIVEN** API down and Catálogo demo
- **WHEN** the operator selects `30+ días`
- **THEN** only mock rows with `coverageBandFromDays(days) === "30+ días"` remain
- **AND** qty still comes from mock `compute()`, never from a second formula
