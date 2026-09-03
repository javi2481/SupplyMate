# Traceability matrix — active changes

Maps each MUST to automated test or manual checklist id.

## mvp-core / replenishment

| MUST | Verification |
|------|----------------|
| avg daily = total/30 | `tests/test_replenishment.py::test_average_daily_demand_from_30_day_total` |
| stock target components | `tests/test_replenishment.py::test_stock_target_components` |
| recommended qty when stock low | `tests/test_replenishment.py::test_stock_target_components` |
| recommended qty = 0 when stock high | `tests/test_replenishment.py::test_recommended_quantity_zero_when_stock_exceeds_target` |
| lead time triangulation | `tests/test_replenishment.py::test_different_lead_time_triangulation` |

## mvp-core / tools

| MUST | Verification |
|------|----------------|
| inventory includes product_id, current_stock | `tests/test_tools.py::test_load_inventory_valid_product` |
| sales history non-empty window | `tests/test_tools.py::test_load_sales_history_valid_product` |
| params include lead_time, safety_stock | `tests/test_tools.py::test_load_replenishment_params_valid` |
| unknown product raises | `tests/test_tools.py::test_load_inventory_unknown_product` |

## mvp-core / agent

| MUST | Verification |
|------|----------------|
| qty equals Python result | `tests/test_agent.py::test_run_supplymate_quantity_matches_python_calc` |
| qty not parsed from LLM text alone | `tests/test_agent.py::test_run_supplymate_quantity_matches_python_calc` |

## mvp-core / api

| MUST | Verification |
|------|----------------|
| chat 200 with answer, product_id, qty | `tests/test_api.py::test_chat_success` |
| replenishment 200 | `tests/test_api.py::test_get_replenishment` |
| chat 404 unknown | `tests/test_api.py::test_chat_not_found` |

## dual-surface / metrics

| MUST | Verification |
|------|----------------|
| canonical labels | `tests/test_metrics.py::test_canonical_labels` |
| days of supply | `tests/test_metrics.py::test_days_of_supply_when_demand_positive` |
| health buckets | `tests/test_metrics.py::test_health_bucket_stockout_risk` |

## dual-surface / purchase-export

| MUST | Verification |
|------|----------------|
| purchase list sorted, qty > 0 | `tests/test_purchase_list.py::test_list_purchase_recommendations_sorted` |
| CSV columns | `tests/test_api.py::test_purchase_list_csv` |

## dual-surface / surfaces (API-backed)

| MUST | Verification |
|------|----------------|
| dashboard KPIs in chat list mode | `tests/test_api.py::test_chat_purchase_list` |
| sales mode by_sales | `tests/test_api.py::test_chat_top_categories` |
| no fabricated trend | design constraint; no trend field in `InventoryDashboard` — `tests/test_dashboard.py::test_from_rows_health_and_charts` |

## interactive-drilldown / scope

| MUST | Verification |
|------|----------------|
| expose scope fields | `tests/test_scope.py::test_scope_from_query_params` |
| add idempotent | `tests/test_scope.py::test_add_idempotent` |
| OR two categories | `tests/test_scope.py::test_add_or_two_categories` |
| limits enforced | `tests/test_scope.py::test_add_respects_limit` |
| remove / reset | `tests/test_scope.py::test_remove_and_reset` |
| cache_key order independent | `tests/test_scope.py::test_cache_key_order_independent` |
| SALES_AS_OF in cache_key | `tests/test_scope.py::test_cache_key_order_independent` |

## interactive-drilldown / slice-api

| MUST | Verification |
|------|----------------|
| slice JSON shape | `tests/test_api.py::test_replenishment_slice_endpoint` |
| query params | `tests/test_api.py::test_slice_with_category_filter` |
| empty filter 200 | `tests/test_api.py::test_slice_empty_category_returns_200` |
| no LLM on slice | no Runner patch needed; `tests/test_catalog_service.py::test_replenishment_slice_empty_evidence` |
| aligned dashboard/list/csv | `tests/test_api.py::test_csv_matches_filtered_list` |
| chat_dashboard(scope) | `tests/test_catalog_service.py::test_chat_dashboard_with_scope_reduces_skus` |

## interactive-drilldown / suggested-filters

| MUST | Verification |
|------|----------------|
| at most 3 | `tests/test_suggested_filters.py::test_suggest_at_most_three` |
| no LLM | `tests/test_suggested_filters.py::test_suggest_at_most_three` |
| values from snap only | `tests/test_suggested_filters.py::test_suggest_skips_active_category` |
| skip active | `tests/test_suggested_filters.py::test_suggest_skips_active_category` |

## interactive-drilldown / filter_rows

| MUST | Verification |
|------|----------------|
| OR same dimension | `tests/test_dashboard.py::test_filter_rows_or_two_categories` |
| AND across dimensions | `tests/test_dashboard.py::test_filter_rows_and_category_plus_coverage` |
| highlight no filter | `tests/test_dashboard.py::test_filter_rows_highlight_does_not_filter` |

## interactive-drilldown / surfaces (manual)

| MUST | Manual id |
|------|-----------|
| live panel interactive charts | UX-01 |
| history static | UX-02 |
| breadcrumb + reset | UX-03 |
| chart click add | UX-04 |
| chip add | UX-05 |
| CSV same params + N label | UX-06 |
| SKU highlight + Cómo se calculó | UX-07 |

## engineering-quality / security

| MUST | Verification |
|------|----------------|
| message max_length | `tests/security/test_security.py::test_chat_message_too_long_returns_422` |
| prod no stack trace | `tests/security/test_security.py::test_production_error_hides_traceback` |
| chat rate limit 429 | `tests/security/test_security.py::test_chat_rate_limit_returns_429` |
| security headers | `tests/security/test_security.py::test_security_headers_present` |
| scope param sanitization | `tests/security/test_security.py::test_oversized_scope_param_rejected` |

## engineering-quality / deployment

| MUST | Verification |
|------|----------------|
| smoke health | `scripts/smoke_api.sh` step 1 |
| smoke slice | `scripts/smoke_api.sh` step 2 |
| smoke csv | `scripts/smoke_api.sh` step 3 |
| smoke SKU 6033436 | `scripts/smoke_api.sh` step 4 |
