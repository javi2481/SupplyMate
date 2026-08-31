# Spec: scope

## Requirements

### AnalyticalScope model

- MUST expose `categories`, `coverage_buckets`, `health_buckets`, `suppliers` (lists) and `highlight_product_id` (string, default empty).

### add

- GIVEN value not already in the dimension list
  WHEN `add(scope, dimension, value)` is called
  THEN the value MUST appear in that list
- GIVEN the same value again
  WHEN `add` is called
  THEN the scope MUST be unchanged (idempotent)
- GIVEN list at limit (5 for cat/coverage/supplier, 4 for health)
  WHEN `add` is called with a new value
  THEN the value MUST be ignored (no error)

### remove and reset

- GIVEN an active filter
  WHEN `remove(scope, dimension, value)` is called
  THEN that value MUST be removed
- WHEN `reset()` is called
  THEN all lists MUST be empty and `highlight_product_id` MUST be empty

### filter_rows

- GIVEN scope with one category
  WHEN `filter_rows` runs
  THEN only rows with that category MUST remain
- GIVEN two categories in scope
  WHEN `filter_rows` runs
  THEN rows matching either category MUST remain (OR)
- GIVEN category and coverage_bucket in scope
  WHEN `filter_rows` runs
  THEN rows MUST match both (AND)
- GIVEN `highlight_product_id` set
  WHEN `filter_rows` runs
  THEN row count MUST NOT change

### cache_key

- GIVEN scopes differing only by list order
  WHEN `cache_key` is computed
  THEN keys MUST be equal
- MUST include `SALES_AS_OF` from store
