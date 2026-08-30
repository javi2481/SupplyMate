# Tasks: dual-surface-analytics

## Phase 1 — Metrics (Strict TDD)

- [x] 1.1 RED/GREEN/TRIANGULATE `days_of_supply`
- [x] 1.2 RED/GREEN/TRIANGULATE `health_bucket` (ROP / understock / overstock / healthy)
- [x] 1.3 Canonical label constants

## Phase 2 — Analytics DB (Strict TDD)

- [x] 2.1 RED/GREEN build DuckDB from fixtures / temp CSV sample
- [x] 2.2 TRIANGULATE `analytics_sku.recommended_quantity` == `calculate_replenishment`
- [x] 2.3 `v_inventory_health` view; gitignore `*.duckdb`

## Phase 3 — Purchase export (Strict TDD)

- [x] 3.1 Enrich `PurchaseListItem` + catalog_service mapping
- [x] 3.2 `GET /replenishment/purchase-list.csv` headers and rows

## Phase 4 — Surfaces

- [x] 4.1 Streamlit chat dashboard (KPIs + category/coverage charts + OC table), no separate Superset UI
- [x] 4.2 Compose + Superset Dockerfile + `docs/analytics-superset.md` (one dashboard)
- [x] 4.3 README dual-surface + `.env.example` SUPERSET_URL

## Phase 5 — Verify

- [x] 5.1 pytest green; verify-report with TDD table + UX checklist
