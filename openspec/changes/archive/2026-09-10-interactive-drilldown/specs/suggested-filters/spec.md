# Spec: suggested-filters

## Requirements

### suggest_next_filters

- MUST return at most 3 `SuggestedFilter` items
- MUST NOT call LLM or `Runner`
- Values MUST come only from the current snap/items (no invented categories or buckets)
- MUST skip filters already active in scope

### Ranking order (first applicable, up to 3)

1. Top `by_category` by `recommended_quantity` not in scope
2. Coverage bucket `"0–3 días"` if `sku_count > 0`, else next populated bucket
3. `filter_health` stockout_risk if snap.stockout_risk > 0 and not active
4. Most frequent supplier in current `purchase_list` items
5. Top purchase_list item → `open_sku`

### SuggestedFilter shape

- `action`: one of `filter_category`, `filter_coverage`, `filter_health`, `filter_supplier`, `open_sku`
- `args`: dict with dimension keys matching action
- `label`: human-readable string from template using snap numbers
