# Spec: slice-api

## Requirements

### GET /replenishment/slice

- MUST return JSON with: `scope`, `evidence`, `dashboard`, `purchase_list`, `suggested_filters`
- MUST accept repeatable query params: `category`, `coverage_bucket`, `health_bucket`, `supplier`, `highlight_product_id`, `limit` (default 25, ge=1, le=100)
- GIVEN filters matching zero SKUs
  WHEN slice is requested
  THEN status MUST be 200 with empty `purchase_list` and empty-state evidence
- MUST NOT call `run_supplymate` or `classify_intent`

### Aligned endpoints

- `GET /replenishment/dashboard`, `GET /replenishment/purchase-list`, `GET /replenishment/purchase-list.csv` MUST accept the same filter query params
- CSV rows MUST match `purchase_list` from slice with identical params (same product_ids and quantities)

### Data source

- Filtered dashboard and list MUST come from `chat_dashboard(limit, scope)` over `_sku_rows_cache`, not unfiltered `list_purchase_recommendations`
