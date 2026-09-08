# Spec: dashboard-totals (delta)

## ADDED Requirements

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
