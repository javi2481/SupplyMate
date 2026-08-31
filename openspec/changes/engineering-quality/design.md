# Design: engineering-quality

## Environment

| Variable | Values | Purpose |
|----------|--------|---------|
| `SUPPLYMATE_ENV` | `development` (default), `production`, `test` | Error detail, rate limits |
| `CHAT_RATE_LIMIT_PER_MIN` | int, default 10 | `/chat` abuse protection |

In `test` env: rate limit disabled (high ceiling) so pytest stays deterministic.

## CI layout

```text
job test     → pytest + cov on app/replenishment.py, app/services/{scope,catalog_service,dashboard}.py
job docker   → docker build + run + scripts/smoke_api.sh
job perf     → main branch only; pytest -m performance
job audit    → pip-audit continue-on-error
```

Coverage fail_under: 85% on critical paths only (baseline-adjusted).

## Security middleware stack

```text
Request → SecurityHeadersMiddleware → ChatRateLimitMiddleware → routes
Exception → production hides stack traces
```

## Traceability

Each MUST in `mvp-core`, `dual-surface-analytics`, `interactive-drilldown` maps to at least one `tests/test_*.py::test_*`. UI-only MUSTs map to manual checklist in verify-report.

## Performance thresholds

- `replenishment_slice(empty, limit=100)` < 3s (CI), < 1.5s local guidance
- Profile: 90% slice reads, 10% chat (documented in `docs/performance-profile.md`)
