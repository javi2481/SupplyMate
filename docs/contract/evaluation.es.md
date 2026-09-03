**Español** · [English](evaluation.md) · [README](../README.md) · [README ES](../README.es.md)

# Evaluación

El harness de evaluación es **re-ejecutable** desde git clone. **Scores Groq live** requieren `RUN_LLM_EVALS=1` y API key real — excluidos del CI.

CI valida contratos, lógica de fórmula, filtros slice e insight validators; **no** afirma calidad de prosa LLM en cada push.

## Qué corre CI

Workflow: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)

| Job | Cuándo | Comando |
|-----|--------|---------|
| `test` | cada push / PR | `pytest -m "not performance and not llm"` + cobertura |
| `docker-smoke` | después de test | build imagen, `/health`, `scripts/smoke_api.sh` |
| `performance` | solo main/master | `pytest -m performance` |

### Gate de cobertura

Fallo bajo **85%** en:

- `app.core.replenishment`
- `app.services.scoping.mutations` (importado como `app.services.scope`)
- `app.services.analytics.catalog_service`
- `app.services.analytics.dashboard`
- `app.pipeline.query_interpretation`
- `app.pipeline.reference_resolver`
- `app.guidance.engine`

Configurado en CI y [`pyproject.toml`](../pyproject.toml) (subconjunto en `[tool.coverage.report]`).

### Markers pytest

| Marker | CI | Propósito |
|--------|-----|-----------|
| (default) | sí | Tests unitarios y API |
| `performance` | solo main | Smoke de latencia slice/dashboard |
| `llm` | no | Evals Groq live |

Correr local:

```bash
pytest -m "not performance and not llm"
pytest -m performance
RUN_LLM_EVALS=1 pytest -m llm
```

## Fixtures golden

CSVs bajo `tests/golden/`:

| Archivo | Cubre |
|---------|-------|
| `golden/intents/golden_intents.csv` | Routing de intención |
| `golden/multiturn/golden_multiturn.csv` | Conversación multiturn |
| `golden/query_interpretation/golden_query_interpretation.csv` | Reglas de interpretación de consulta |
| `golden/reference_resolution/golden_reference_resolution.csv` | Resolución SKU / nombre / barcode |

Tests: `golden/intents/test_golden_intents.py`, `golden/multiturn/test_golden_multiturn.py`, `golden/query_interpretation/test_golden_query_interpretation.py`, `golden/reference_resolution/test_golden_reference_resolution.py`.

Layout: [`tests/README.md`](../tests/README.md).

## Evals de insight y analyze

- [`app/services/insight_validator.py`](../app/services/insight_validator.py) — rechaza enteros huérfanos, SKUs desconocidos, prioridades inválidas
- [`tests/unit/insight_validator/test_insight_validator.py`](../tests/unit/insight_validator/test_insight_validator.py) — checks de schema y hechos
- [`tests/integration/api/test_analyze_api.py`](../tests/integration/api/test_analyze_api.py) — contrato `/replenishment/analyze`

Si el validator falla, los agentes caen a texto determinístico — los números del slice siguen siendo de Python.

## Smoke de rendimiento

Umbrales en [`docs/operations/performance-profile.md`](performance-profile.md):

| Operación | Umbral CI |
|-----------|-----------|
| `replenishment_slice(limit=100)` | < 3 s |
| `chat_dashboard(limit=100)` | < 3 s |

Primera carga construye `_sku_rows_cache` — incluida en medición. Latencia Groq excluida (mock en tests).

## Qué no afirmamos

- CI **no** prueba accuracy LLM 100%.
- CI **sí** prueba fórmula order-up-to, paridad slice/scope con CSV, golden intents y contratos del validator.
