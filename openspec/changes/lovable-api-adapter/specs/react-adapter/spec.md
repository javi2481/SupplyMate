# Spec: react-adapter

## ADDED Requirements

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
