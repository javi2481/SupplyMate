# Proposal: KPI totals from the full recorte

## Why

Explore KPIs mix two grains. `Productos` / health counts come from
`InventoryDashboard` (every SKU in the AnalyticalScope). `Unidades a pedir`
sums the `purchase_list` page (`limit=50`). The category chart uses
`dashboard.by_category` over the full recorte (top 8). Operators see e.g.
1,059 productos, 6,243 unidades in the KPI, 17,753 on the chart, and 50 table
rows.

Python already owns replenishment math. The dashboard must also own recorte
totals. The table stays a ranked sample.

## What changes

- `InventoryDashboard` exposes `recommended_units` (sum of recommended qty in
  the recorte) and `purchase_skus` (SKUs with qty > 0).
- Explore KPI `Unidades a pedir` and OC header units/value/SKU counts read
  those dashboard fields when the API is up.
- The table caption distinguishes the page (`limit`) from `purchase_skus`.
- Mock / Catálogo demo still sums the in-memory catalog (small).

## Out of scope

- Raising `purchase_list` / CSV `limit` to the full recorte.
- Chart showing every category (ranking of top 8 stays).
- `Falta de stock` KPI vs `sin_stock` chip (`understock` bucket vs stock === 0).
- Seed chat threads, SSR “Catálogo demo” flash, auth.
- Splitting `index.tsx`.
