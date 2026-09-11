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

- `app.core.replenishment`
- `app.services.scoping.mutations` (imported as `app.services.scope`)
- `app.services.analytics.catalog_service`
- `app.services.analytics.dashboard`
- `app.pipeline.query_interpretation`
- `app.pipeline.reference_resolver`
- `app.guidance.engine`

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

CSV fixtures under `tests/golden/`:

| File | Rows (frozen) | Covers |
|------|---------------|--------|
| `golden/intents/golden_intents.csv` | 35 | Intent routing |
| `golden/multiturn/golden_multiturn.csv` | 4 | Multi-turn conversation |
| `golden/query_interpretation/golden_query_interpretation.csv` | 10 | Query interpretation rules |
| `golden/reference_resolution/golden_reference_resolution.csv` | 16 | SKU / name / barcode resolution |

These four legacy CSVs are **frozen in row count**. `tests/golden/test_frozen_golden_counts.py` guards the counts (including the header row). Add new regression strings to `tests/golden/traps/traps.csv` or a generated recorte contract — do not grow the legacy files.

Tests: `golden/intents/test_golden_intents.py`, `golden/multiturn/test_golden_multiturn.py`, `golden/query_interpretation/test_golden_query_interpretation.py`, `golden/reference_resolution/test_golden_reference_resolution.py`, `golden/traps/test_traps.py`, `golden/test_frozen_golden_counts.py`.

Layout overview: [`tests/README.md`](../tests/README.md).

## Recorte oracle and traps

SupplyMate scores chat behavior with **Python oracle predicates**, not LLM judges. Groq may paraphrase inputs in opt-in `@pytest.mark.llm` runs; assertions always read structured surfaces (`ResolvedReference`, `AnalyticalScope`, `ReplenishmentSlice`, `ChatResponse`, frontend `applyChatScope`).

| Surface | What we assert |
|---------|----------------|
| Reference resolution | `match_kind`, `scope_dimension`, containment vs name hits |
| Scope build | Dimension exclusivity, refinement vs `new_query`, horizon echo |
| Replenishment slice | Emptiness equivalence, no `draft_oc` on empty recorte |
| Explore answer | Structural numeric-claim probe — never a stored sentence |
| Thread cart (Vitest) | Multi-rubro merge, sales no-op, refinement drops only the refined category |

**Traps** (`tests/golden/traps/traps.csv`): concrete strings frozen only for bugs we have seen (unresolved supplier token, size-token confusion, empty-purchase copy, documented name-hit sets). Columns: `name, message, previous_scope, surface, assertion, issue`. Trap tests call the same oracle helpers — no answer-text goldens.

A full combinatorial recorte harness (catalog-driven axes, pairwise coverage, seed + cap, `combinatorial_full` opt-in, catalog-shape drift snapshot) lives under `tests/evals/recorte/` when enabled; CI runs traps and frozen goldens without outbound model requests.

**Cart note:** the chat thread cart (Vitest in `frontend/src/lib/cart.test.ts` and `chatTurn.test.ts`) accumulates purchase turns across categories; sales turns and empty `purchase_list` responses do not add lines.

## Insight and analyze evals

- [`app/services/insight/insight_validator.py`](../../app/services/insight/insight_validator.py) — rejects orphan integers, unknown SKUs, invalid priorities
- [`tests/unit/insight_validator/test_insight_validator.py`](../tests/unit/insight_validator/test_insight_validator.py) — schema and fact checks
- [`tests/integration/api/test_analyze_api.py`](../tests/integration/api/test_analyze_api.py) — `/replenishment/analyze` contract

On validator failure, agents fall back to deterministic text — slice numbers stay Python-owned.

## Performance smoke

Thresholds in [`docs/operations/performance-profile.md`](performance-profile.md):

| Operation | CI threshold |
|-----------|--------------|
| `replenishment_slice(limit=100)` | < 3 s |
| `chat_dashboard(limit=100)` | < 3 s |

First load builds `_sku_rows_cache` — included in measurement. Groq latency excluded (mocked in tests).

## What we do not claim

- CI does **not** prove 100% LLM answer accuracy.
- CI **does** prove order-up-to formula, slice/scope parity with CSV, golden intents, and validator contracts.
