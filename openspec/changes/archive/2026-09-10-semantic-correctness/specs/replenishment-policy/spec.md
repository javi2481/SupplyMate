# Spec: replenishment-policy

## Requirements

### Order-up-to quantity

- GIVEN average daily demand D, lead time L, safety stock SS, on-hand S
  WHEN `calculate_replenishment` runs
  THEN `stock_target` MUST equal `D*7 + D*L + SS`
  AND `recommended_quantity` MUST equal `max(0, ceil(stock_target - S))`
  AND MUST NOT use `reorder_point`

### Fractional remainder

- GIVEN `stock_target - current_stock` is 41.8
  THEN `recommended_quantity` MUST be 42
