# Spec: metrics

## Purpose

Define shared inventory analytics metrics used by DuckDB materialization and purchase-list enrichment.

## Canonical labels

The system MUST use these display labels:

| Key | Label |
|-----|-------|
| stockout_risk | Stockout Risk |
| understock | Understock |
| overstock | Overstock |
| healthy | Healthy |
| coverage | Coverage |
| recommended_qty | Recommended Qty |

## Requirements

### Days of supply

- GIVEN current stock S and average daily demand D > 0
  WHEN `days_of_supply` is computed
  THEN it MUST equal S / D
- GIVEN D = 0
  WHEN `days_of_supply` is computed
  THEN it MUST be null / None

### Health bucket

- GIVEN recommended_quantity > 0 AND current_stock ≤ reorder_point
  THEN health_bucket MUST be `stockout_risk`
- GIVEN recommended_quantity > 0 AND NOT (stock ≤ reorder_point)
  THEN health_bucket MUST be `understock`
- GIVEN recommended_quantity = 0 AND max_stock is set AND stock > max_stock
  THEN health_bucket MUST be `overstock`
- GIVEN otherwise
  THEN health_bucket MUST be `healthy`

### Parity with replenishment

- GIVEN a product master and `calculate_replenishment` result
  WHEN building an analytics row
  THEN `recommended_quantity` MUST equal the Python formula result (MUST NOT invent qty)
