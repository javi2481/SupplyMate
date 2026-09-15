**Español** · [English](evaluation.md) · [README](../README.md) · [README ES](../README.es.md)

# Evaluación

El harness de evaluación es **re-ejecutable** desde git clone. **Scores LLM paraphrase live** requieren `RUN_LLM_EVALS=1` y API key real (Groq / DeepSeek / OpenAI) — excluidos del CI.

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
| `llm` | no | Evals LLM paraphrase live |

Correr local:

```bash
pytest -m "not performance and not llm"
pytest -m performance
RUN_LLM_EVALS=1 pytest -m llm
```

## Fixtures golden

CSVs bajo `tests/golden/`:

| Archivo | Filas (congeladas) | Cubre |
|---------|-------------------|-------|
| `golden/intents/golden_intents.csv` | 35 | Routing de intención |
| `golden/multiturn/golden_multiturn.csv` | 4 | Conversación multiturn |
| `golden/query_interpretation/golden_query_interpretation.csv` | 10 | Reglas de interpretación de consulta |
| `golden/reference_resolution/golden_reference_resolution.csv` | 16 | Resolución SKU / nombre / barcode |

Estos cuatro CSVs legacy están **congelados en cantidad de filas**. `tests/golden/test_frozen_golden_counts.py` protege los conteos (incluido el header). Casos nuevos van en `tests/golden/traps/traps.csv`, `tests/golden/traps/resolution_cases.csv` o en un contrato generado — no agrandar los archivos legacy.

Tests: `golden/intents/test_golden_intents.py`, `golden/multiturn/test_golden_multiturn.py`, `golden/query_interpretation/test_golden_query_interpretation.py`, `golden/reference_resolution/test_golden_reference_resolution.py`, `golden/traps/test_traps.py`, `golden/traps/test_resolution_cases.py`, `golden/test_frozen_golden_counts.py`.

Layout: [`tests/README.md`](../tests/README.md).

## Oráculo de recorte y traps

SupplyMate puntúa el chat con **predicados oráculo en Python**, no con jueces LLM. Un provider configurado puede parafrasear entradas en corridas opt-in `@pytest.mark.llm`; las aserciones leen superficies estructuradas (`ResolvedReference`, `AnalyticalScope`, `ReplenishmentSlice`, `ChatResponse`, `applyChatScope` en frontend).

| Superficie | Qué afirmamos |
|------------|---------------|
| Resolución de referencias | `match_kind`, `scope_dimension`, contención vs name hits |
| Scope | Exclusividad de dimensión, refinement vs `new_query`, eco de horizonte |
| Slice de reposición | Equivalencia de vacío, sin `draft_oc` en recorte vacío |
| Respuesta explore | Sonda estructural de claims numéricos — nunca una frase golden |
| Carrito del hilo (Vitest) | Merge multi-rubro, sales no-op, refinement solo en la categoría refinada |

**Traps** (`tests/golden/traps/traps.csv`): strings concretos congelados solo para bugs vistos (token proveedor no resuelto, confusión de size token, copy con purchase vacío, conjuntos name-hit documentados). Columnas: `name, message, previous_scope, surface, assertion, issue`. Los tests de trap llaman los mismos helpers del oráculo — sin goldens de texto de respuesta.

**Casos de resolución** (`tests/golden/traps/resolution_cases.csv`): contratos vernáculo → taxonomía del catálogo (`match_kind`, `scope_dimension`, `scope_value`) vía `resolve_single_reference` — no se delegan al intérprete LLM, que solo conserva lo que dijo el operador.

Un harness combinatorial completo (ejes driven por catálogo, cobertura pairwise, seed + cap, opt-in `combinatorial_full`, snapshot de forma del catálogo) vive en `tests/evals/recorte/` cuando está habilitado; CI corre traps y goldens congelados sin requests al modelo.

**Nota carrito:** el carrito del hilo (Vitest en `frontend/src/lib/cart.test.ts` y `chatTurn.test.ts`) acumula turnos de compra entre categorías; turnos sales y `purchase_list` vacío no agregan líneas.

## Evals de insight y analyze

- [`app/services/insight/insight_validator.py`](../../app/services/insight/insight_validator.py) — rechaza enteros huérfanos, SKUs desconocidos, prioridades inválidas
- [`tests/unit/insight_validator/test_insight_validator.py`](../tests/unit/insight_validator/test_insight_validator.py) — checks de schema y hechos
- [`tests/integration/api/test_analyze_api.py`](../tests/integration/api/test_analyze_api.py) — contrato `/replenishment/analyze`

Si el validator falla, los agentes caen a texto determinístico — los números del slice siguen siendo de Python.

## Smoke de rendimiento

Umbrales en [`docs/operations/performance-profile.md`](performance-profile.md):

| Operación | Umbral CI |
|-----------|-----------|
| `replenishment_slice(limit=100)` | < 3 s |
| `chat_dashboard(limit=100)` | < 3 s |

Primera carga construye `_sku_rows_cache` — incluida en medición. Latencia del provider LLM excluida (mock en tests).

## Presupuesto de interpretación LLM

La interpretación es **rules-first**. Los patrones conocidos no llaman al modelo (`test_interpret_query_rules_first_skips_llm`). Frases ambiguas pueden ir al LLM; ante timeout el servidor **abandona** la tarea en vuelo y cae a rules (`asyncio.wait` + abandon — no `wait_for` que espera el cancel).

| Perilla | Default | Rol |
|---------|---------|-----|
| `LLM_INTERPRET_TIMEOUT_SEC` | 15 | Presupuesto de abandon en interpret / intent classify |
| `LLM_HTTP_TIMEOUT_SEC` | 20 | Timeout HTTP del client (debe quedar bajo el abort de UI) |
| Abort frontend `/chat` | 25 s (`CHAT_FETCH_TIMEOUT_MS`) | `AbortSignal.timeout` para que la UI no cuelgue en un LLM zombie |

**Regresión:** un `/chat` por rules (sin LLM) que tarde **> 5 s** es hang, no “modelo lento”. Mirar `logs/chat-turns.jsonl` / `trace` de la respuesta / `[SupplyMate turn]` en el browser antes de tocar UI.

Checklist de coherencia del panel (label ≡ scope ≡ KPI ≡ chart ≡ tabla ≡ CTA/OC): [`docs/operations/recorte-coherence.md`](../operations/recorte-coherence.md).

## Qué no afirmamos

- CI **no** prueba accuracy LLM 100%.
- CI **sí** prueba fórmula order-up-to, paridad slice/scope con CSV, golden intents y contratos del validator.
