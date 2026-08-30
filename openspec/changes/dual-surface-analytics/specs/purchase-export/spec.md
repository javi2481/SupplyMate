# Spec: purchase-export

## Purpose

Support the operation surface: enriched purchase list and CSV purchase-order export.

## Requirements

### Enriched list item

- GIVEN purchase recommendations
  WHEN returned as `PurchaseListItem`
  THEN each item MUST include at least:
  product_id, barcode, product_name, supplier, category, current_stock,
  reorder_point, average_daily_demand, days_of_supply, health_bucket, recommended_quantity

### CSV export

- GIVEN `GET /replenishment/purchase-list.csv`
  THEN the response MUST be `text/csv`
  AND columns MUST be exactly:
  `barcode,product_id,product_name,supplier,recommended_quantity`
  AND row quantities MUST match the enriched list for the same limit

### No product analytics health API

- The product surface MUST NOT expose a competing `/analytics/health` dashboard endpoint for UI use
