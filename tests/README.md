# Test layout

Tests are grouped by layer so `pytest --collect-only` and CI logs stay scannable.

```
tests/
├── unit/                    # isolated module behavior
│   ├── replenishment/
│   ├── metrics/
│   ├── dashboard/           # + suggested filters
│   ├── scope/
│   ├── catalog/             # product tools + dependency architecture constraints
│   ├── store/
│   ├── prompt_compiler/
│   ├── intent_classifier/
│   ├── insight_validator/
│   ├── insight_cache/
│   ├── purchase_list/
│   ├── guidance/            # preview_union and related helpers
│   └── llm_log/
├── integration/             # cross-module flows
│   ├── api/                 # FastAPI + analyze endpoints
│   ├── pipeline/            # interpret → resolve → scope → slice
│   ├── agent/
│   ├── query_interpretation/
│   ├── reference_resolution/
│   ├── conversation/
│   ├── guidance/
│   └── purchase_flow/       # explore / commit panel modes
├── contract/
│   └── api_contract/
├── acceptance/              # end-to-end business scenarios
├── property/                # Hypothesis property-based
│   ├── replenishment/
│   └── scope/
├── golden/                  # CSV-driven eval fixtures
│   ├── intents/
│   ├── multiturn/
│   ├── query_interpretation/   # test_golden_query_interpretation.py
│   └── reference_resolution/   # test_golden_reference_resolution.py
├── security/
├── performance/
└── regression/              # known historical behaviors
```

Shared helpers: `conftest.py`, `catalog_ids.py` (stable SKU ids for the real catalog).

Run the default CI suite:

```bash
pytest -m "not performance and not llm"
```

Run one layer:

```bash
pytest tests/unit/
pytest tests/integration/
pytest tests/golden/
```
