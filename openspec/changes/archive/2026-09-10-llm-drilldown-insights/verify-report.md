# Verify: llm-drilldown-insights

| MUST | Test |
|------|------|
| POST /analyze explore | test_analyze_explore_returns_200 |
| POST /analyze commit requires frozen_scope | test_analyze_commit_requires_frozen_scope |
| Validator rejects invented SKU | test_validate_insight_rejects_unknown_sku |
| Export gate explore=false | test_can_export_only_in_commit |
| Rate limit /analyze | test_analyze_rate_limit_429 |
| Fallback on bad JSON | test_analyze_invalid_llm_json_fallback |

**pytest:** 148 passed, 1 skipped (2026-08-30)
