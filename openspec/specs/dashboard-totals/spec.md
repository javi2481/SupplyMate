# Spec: dashboard-totals

## Requirements

### Requirement: Dashboard exposes recorte purchase totals

`InventoryDashboard` MUST include `recommended_units` (sum of
`recommended_quantity` over scoped rows) and `purchase_skus` (count of scoped
rows with `recommended_quantity > 0`). These MUST be computed in
`from_rows`, not from the truncated `purchase_list`.

#### Scenario: Totals ignore purchase_list limit

- **GIVEN** five scoped rows with recommended quantities 20, 5, 0, 0, 0
- **WHEN** `from_rows` builds the dashboard
- **THEN** `recommended_units` MUST be 25
- **AND** `purchase_skus` MUST be 2
- **AND** `purchase_items(..., limit=1)` MUST NOT change those totals

### Requirement: Dashboard exposes out_of_stock count

`InventoryDashboard` MUST include `out_of_stock` as the count of scoped rows
with `current_stock == 0`. This is distinct from the `understock` health bucket.

#### Scenario: Zero stock rows

- **GIVEN** scoped rows with current_stock values 0, 0, 5, 10
- **WHEN** `from_rows` builds the dashboard
- **THEN** `out_of_stock` MUST be 2

### Requirement: Scope filters by out_of_stock_only

`AnalyticalScope` MUST support `out_of_stock_only`. When true, `filter_rows`
MUST keep only rows with `current_stock == 0`. The FastAPI query param MUST be
`out_of_stock=true` (boolean), not a `health_bucket` value.

#### Scenario: Query out_of_stock=true

- **GIVEN** a slice request with `out_of_stock=true`
- **WHEN** the scoped dashboard is built
- **THEN** every remaining row MUST have `current_stock == 0`
