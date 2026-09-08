# Tasks: kpi-recorte-totals

## Phase 1 — TDD backend

- [x] 1.1 RED: `from_rows` asserts `recommended_units` / `purchase_skus`
- [x] 1.2 GREEN: add fields on `InventoryDashboard` and populate in `from_rows`
- [x] 1.3 RED/GREEN contract: slice `recommended_units >= sum(purchase_list qty)` when limit=50

## Phase 2 — TDD frontend

- [x] 2.1 RED: `kpisFromDashboard` uses `recommended_units`, not the list sum
- [x] 2.2 GREEN: wire Explore KPI Unidades, table caption, OC header
- [x] 2.3 Caption helper: page vs `purchase_skus`

## Phase 3 — Verify

- [x] 3.1 `npm test` + `pytest tests/unit/dashboard/ tests/contract/api_contract/`
- [x] 3.2 Manual Motor listo: Unidades KPI matches chart magnitude, table says 50 de N
- [x] 3.3 `graphify update .`
