**English** · [Español](evaluation.es.md) · [README](../README.md) · [README ES](../README.es.md)

# Evaluation

The evaluation harness is **re-runnable** from git clone. **Live Groq scores** require `RUN_LLM_EVALS=1` and a real API key — excluded from CI.

CI validates contracts, formula logic, slice filters, and insight validators; it does **not** assert LLM prose quality on every push.

## What CI runs

Workflow: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)

| Job | When | Command |
|-----|------|---------|
| `test` | every push / PR | `pytest -m "not performance and not llm"` + coverage |
| `docker-smoke` | after test | build image, `/health`, `scripts/smoke_api.sh` |
| `performance` | main/master only | `pytest -m performance` |

### Coverage gate

Fail under **85%** on:

- `app.replenishment`
- `app.services.scope`
- `app.services.catalog_service`
- `app.services.dashboard`
- `app.query_interpretation`
- `app.reference_resolver`
- `app.guidance`

Configured in CI and [`pyproject.toml`](../pyproject.toml) (subset in `[tool.coverage.report]`).

### Pytest markers

| Marker | CI | Purpose |
|--------|-----|---------|
| (default) | yes | Unit and API tests |
| `performance` | main only | Slice/dashboard latency smoke |
| `llm` | no | Live Groq evals |

Run locally:

```bash
pytest -m "not performance and not llm"
pytest -m performance
RUN_LLM_EVALS=1 pytest -m llm
```

## Golden fixtures

CSV fixtures under `tests/`:

| File | Covers |
|------|--------|
| `golden_intents.csv` | Intent routing |
| `golden_multiturn.csv` | Multi-turn conversation |
| `golden_query_interpretation.csv` | Query interpretation rules |
| `golden_reference_resolution.csv` | SKU / name / barcode resolution |

Tests: `test_golden_intents.py`, `test_golden_multiturn.py`, `test_query_interpretation.py`, `test_reference_resolver.py`.

## Insight and analyze evals

- [`app/services/insight_validator.py`](../app/services/insight_validator.py) — rejects orphan integers, unknown SKUs, invalid priorities
- [`tests/test_insight_validator.py`](../tests/test_insight_validator.py) — schema and fact checks
- [`tests/test_analyze_api.py`](../tests/test_analyze_api.py) — `/replenishment/analyze` contract

On validator failure, agents fall back to deterministic text — slice numbers stay Python-owned.

## Performance smoke

Thresholds in [`docs/performance-profile.md`](performance-profile.md):

| Operation | CI threshold |
|-----------|--------------|
| `replenishment_slice(limit=100)` | < 3 s |
| `chat_dashboard(limit=100)` | < 3 s |

First load builds `_sku_rows_cache` — included in measurement. Groq latency excluded (mocked in tests).

## What we do not claim

- CI does **not** prove 100% LLM answer accuracy.
- CI **does** prove order-up-to formula, slice/scope parity with CSV, golden intents, and validator contracts.
