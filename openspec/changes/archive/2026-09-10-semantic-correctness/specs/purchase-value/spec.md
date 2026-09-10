# Spec: purchase-value

## Requirements

### Cost basis

- GIVEN `ProductMaster.price` is set
  THEN `purchase_cost` MUST equal that price
  AND `estimated_purchase_value` MUST equal `recommended_quantity * purchase_cost`
  AND MUST NOT use `pvp`

### Operational priority

- GIVEN `health_bucket == stockout_risk`
  THEN `operational_priority` MUST be `critical`
- GIVEN recommended qty > 0 AND days of supply < 7 AND not stockout_risk
  THEN `operational_priority` MUST be `high`
- GIVEN otherwise
  THEN `operational_priority` MUST be `normal`

### CSV

- GIVEN purchase-list CSV export
  THEN headers MUST include `operational_priority` and `estimated_purchase_value`
