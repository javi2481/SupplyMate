# Application layout

SupplyMate runtime code lives under `app/`. Layers mirror the test suite (`tests/README.md`) so you can jump from behavior to implementation.

```
app/
├── api.py                 # FastAPI entrypoint (port 8000)
├── core/                  # domain truth — no LLM
│   ├── models.py          # Pydantic contracts (AnalyticalScope, ChatResponse, …)
│   ├── config.py          # paths, env, limits
│   └── replenishment.py   # order-up-to formula (qty owner)
├── catalog/               # CSV evidence load + product resolution
│   ├── store.py           # CatalogStore, in-memory indexes
│   ├── products.py        # resolve_product_id, message SKU heuristics
│   └── store_xlsx.py      # optional XLSX → CSV export helper
├── pipeline/              # interpret → resolve → scope (deterministic)
│   ├── query_interpretation.py
│   ├── reference_resolver.py
│   ├── scope_builder.py
│   └── query_interpreter_agent.py   # LLM fallback for ambiguous text
├── guidance/              # guided selling after a slice
│   ├── engine.py          # next question, draft OC, complement logic
│   ├── guidance_chips.py
│   ├── guidance_tokens.py
│   ├── missions.py        # curated complement graph (data/missions.csv)
│   └── slice_facets.py
├── agent/                 # LLM orchestration (narration only for qty)
│   ├── runner.py          # run_supplymate, run_analyze, run_apply_chip
│   ├── tools.py           # 3 inventory tools for single-SKU path
│   ├── explore_answer.py
│   ├── intents.py         # regex intent rules
│   ├── intent_classifier.py
│   └── llm_log.py
├── services/
│   ├── analytics/         # slice, dashboard, metrics over catalog rows
│   │   ├── catalog_service.py
│   │   ├── dashboard.py
│   │   └── metrics.py
│   ├── scoping/           # scope mutations + UI helpers
│   │   ├── mutations.py   # add/remove/reset AnalyticalScope (import as app.services.scope)
│   │   ├── scope_sanitize.py
│   │   ├── panel_modes.py # explore vs commit
│   │   └── suggested_filters.py
│   └── insight/           # LLM insight path
│       ├── insight_validator.py
│       ├── insight_cache.py
│       └── prompt_compiler.py
└── middleware/            # rate limit, security headers, safe errors
```

## Layer rules

| Layer | Owns | Must not |
|-------|------|----------|
| **core** | qty formula, shared models | Call LLM or Streamlit |
| **catalog** | Load CSV, resolve SKU/name | Filter slices or narrate |
| **pipeline** | Parse user text → scope | Compute replenishment qty |
| **guidance** | Chips, missions, next question | Change catalog evidence |
| **agent** | Intent, explain, insight prose | Override Python qty |
| **services/analytics** | Slice KPIs, purchase list rows | Invent numbers outside CSV |
| **services/scoping** | Scope state, export guardrails | LLM calls |
| **services/insight** | Prompt + validate LLM JSON | Skip validator on commit |

## Import conventions

- Public agent API: `from app.agent import run_supplymate`
- Public guidance API: `from app.guidance import pick_next_question`
- Services (lazy re-export): `from app.services import catalog_service, scope`
- Scope mutations module: `app.services.scoping.mutations` (exposed as `app.services.scope`)

See [`docs/contract/architecture.md`](../docs/contract/architecture.md) for the full technical contract.
