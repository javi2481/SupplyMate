# Design: KPI recorte totals

## Data owner

`dashboard.from_rows(scoped_rows)` already walks every SKU in the recorte.
Add two aggregates next to `skus` / `estimated_purchase_value`:

- `recommended_units = sum(recommended_quantity)`
- `purchase_skus = count(recommended_quantity > 0)`

Reuse `total_recommended_qty()`. Do not sum `purchase_list` in TypeScript on
the happy path.

## UI

| Surface | API up | Catálogo demo |
|---|---|---|
| KPI Unidades | `dashboard.recommended_units` | sum of mock rows |
| KPI Productos | `dashboard.skus` (unchanged) | mock row count |
| Table caption | `page of purchase_skus a reponer` when truncated | `N productos` |
| OC Productos / Unidades / Valor | `purchase_skus` / `recommended_units` / `estimated_purchase_value` | sum of mock PO rows |

The chart remains a ranking (`by_category` top 8). It must not be treated as
the unit total.

## Tests

- Unit: `from_rows` totals independent of `purchase_items(limit)`.
- Vitest: `kpisFromDashboard` uses `recommended_units`, not the list sum.
- Contract: with `limit=50` on the live catalog, `recommended_units >= sum(purchase_list qty)`.
