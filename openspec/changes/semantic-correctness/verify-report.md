# Verify report — semantic-correctness

## Spec coverage

| Spec | Evidence |
|------|----------|
| embeddings-perimeter | `tests/test_tools.py::test_products_module_has_no_sentence_transformers`; pyproject without sentence-transformers/numpy |
| replenishment-policy | `tests/test_replenishment.py::test_ceil_rounds_fractional_gap_up`, `test_policy_does_not_use_reorder_point` |
| metric-contracts | `tests/test_metrics.py::test_metric_contracts_caveats` |
| llm-evals | `tests/test_golden_intents.py`, `tests/test_insight_validator.py`, `test_explain_orphan_falls_back_to_deterministic_text` |
| purchase-value | `tests/test_metrics.py::test_purchase_value_uses_price_not_pvp`, `tests/test_catalog_service.py::test_purchase_list_csv_headers_include_value_and_priority` |

## TDD / CI

- Suite: `pytest -m "not performance and not llm"`
- Coverage ≥85% on replenishment, scope, catalog_service, dashboard
- Marker `llm` excluded from GitHub Actions
- Demo SKU `6033436` re-pinned to **173** after `ceil`

## Verdict

Pass. `pytest -m "not performance and not llm"`: 165 passed. Coverage 95% on critical modules. Docker image smoke on :8001: qty 173, CSV headers include priority/value, no sentence-transformers in the image install.
