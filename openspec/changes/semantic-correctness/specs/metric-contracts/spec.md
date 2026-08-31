# Spec: metric-contracts

## Requirements

### Canonical caveats

- GIVEN metric key `coverage`
  THEN the contract MUST state it is days of supply under constant 30-day average demand, not a forecast
- GIVEN metric key `stockout_risk`
  THEN the contract MUST state it is the rule `recommended_quantity > 0 AND stock <= reorder_point`, not a probability
- GIVEN metric key `overstock`
  THEN the contract MUST state it is stock above max with qty 0, not dead stock

### Reorder point display

- GIVEN a SKU highlight in the UI
  THEN “Punto de reorden” MUST be captioned as a health alarm that does not enter recommended quantity
