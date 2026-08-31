# Graph Report - SupplyMate  (2026-08-31)

## Corpus Check
- 133 files · ~35,344 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1084 nodes · 2107 edges · 93 communities (72 shown, 16 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 139 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5681fff8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- date
- dashboard.py
- agent.py
- store.py
- models.py
- test_analyze_api.py
- bug_report.md
- test_api.py
- test_purchase_list.py
- AnalyticalScope
- export_catalog_csvs.py
- app/__init__.py
- supplymate
- graphify
- Traceability matrix — active changes
- SupplyMate
- Agent
- components.py
- charts.py
- Requirements
- Tasks: engineering-quality
- Proposal: interactive-drilldown
- Protocolo de prueba beta — SupplyMate
- Design: interactive-drilldown
- Requirements
- Tasks: interactive-drilldown
- Plantilla — solicitud de cambio
- Design: engineering-quality
- Security spec (OWASP-minimal)
- Verify report — engineering-quality
- Política de mantenimiento — SupplyMate
- Proposal: engineering-quality
- Requirements
- Requirements
- Design: natural-query-interpretation
- analyst.py
- Perfil operativo — rendimiento
- Proposal: llm-drilldown-insights
- Deployment spec
- Design: llm-drilldown-insights
- CI spec
- Traceability spec
- llm-drilldown-insights/tasks.md
- llm-drilldown-insights/verify-report.md
- smoke_api.sh script
- asyncio
- ProductMaster
- interpret_query_rules
- PanelMode
- ADDED Requirements
- ADDED Requirements
- ProductNotFoundError
- Requirements
- ADDED Requirements
- Proposal: dual-surface-analytics
- Requirements
- Design: mvp-core
- Proposal: mvp-core
- Tasks: mvp-core
- API simulada — contrato de datos SupplyMate
- Design: dual-surface-analytics
- Requirements
- Tasks: dual-surface-analytics
- Verify report — dual-surface-analytics
- Tasks: semantic-correctness
- Requirements
- ADDED Requirements
- Verify Report: mvp-core
- Requirements
- Requirements
- Matriz de compatibilidad
- Verify report — catalog-integration
- Design: semantic-correctness
- Proposal: semantic-correctness
- Requirements
- Requirements
- Requirements
- Verify report — semantic-correctness
- Skill Registry
- Catalog integration — extends mvp-core with unified master + REST
- parametrize
- Any
- Tasks: natural-query-interpretation
- Response
- Proposal: natural-query-interpretation
- SecurityHeadersMiddleware
- Verify report — interactive-drilldown
- Verify: natural-query-interpretation

## God Nodes (most connected - your core abstractions)
1. `AnalyticalScope` - 86 edges
2. `run_supplymate()` - 35 edges
3. `ProductNotFoundError` - 29 edges
4. `run_analyze()` - 28 edges
5. `ProductMaster` - 28 edges
6. `PurchaseListItem` - 22 edges
7. `get_replenishment_recommendation()` - 22 edges
8. `CatalogStore` - 22 edges
9. `get_store()` - 22 edges
10. `Design: natural-query-interpretation` - 22 edges

## Surprising Connections (you probably didn't know these)
- `test_run_analyze_priorities_subset_of_purchase_list()` --uses--> `AnalyticalScope`  [INFERRED]
  tests/test_agent.py → app/models.py
- `test_analyze_commit_requires_frozen_scope()` --calls--> `AnalyticalScope`  [EXTRACTED]
  tests/test_analyze_api.py → app/models.py
- `test_analyze_invalid_llm_json_fallback()` --calls--> `AnalyticalScope`  [EXTRACTED]
  tests/test_analyze_api.py → app/models.py
- `fetch_analyze()` --uses--> `InteractionEvent`  [INFERRED]
  ui/streamlit_app.py → app/models.py
- `test_llm_unknown_does_not_force_a_random_sku()` --uses--> `ProductNotFoundError`  [INFERRED]
  tests/test_agent.py → app/models.py

## Import Cycles
- None detected.

## Communities (93 total, 16 thin omitted)

### Community 1 - "dashboard.py"
Cohesion: 0.17
Nodes (23): CategorySalesBar, coverage_bucket(), filter_rows(), from_rows(), purchase_items(), Inventory dashboard for the Streamlit chat — same metrics as Python…, _row_category(), _row_subcategory() (+15 more)

### Community 2 - "agent.py"
Cohesion: 0.07
Nodes (65): Agent, build_commit_agent(), build_explain_agent(), build_insight_agent(), build_supply_agent(), get_model(), _hydrate_context(), Route by interpreted intent + catalog resolution, then deterministic Python. (+57 more)

### Community 3 - "store.py"
Cohesion: 0.16
Nodes (19): ProductSearchHit, _as_float(), _as_int(), _as_str(), _build_master(), CatalogStore, _expand_sales(), _index_barcodes() (+11 more)

### Community 4 - "models.py"
Cohesion: 0.05
Nodes (98): _fallback_analyze_response(), _parse_json_output(), run_analyze(), _run_purchase_list(), _run_top_categories(), chat(), get_product(), get_replenishment() (+90 more)

### Community 5 - "test_analyze_api.py"
Cohesion: 0.06
Nodes (36): _scope_dependency(), _validate_scope_values(), effective_analyze_rate_limit(), effective_chat_rate_limit(), is_production(), is_test_env(), ChatRateLimitMiddleware, BaseHTTPMiddleware (+28 more)

### Community 6 - "bug_report.md"
Cohesion: 0.11
Nodes (16): Auditoría OSSTMM lite — Sección C (Internet), C — Seguridad en tecnologías de Internet, Fuera de alcance (OSSTMM D–F), Próximos pasos (producción), Actualización, Auditoría local, Dependencias y auditoría (OWASP A06), Pinning (+8 more)

### Community 7 - "test_api.py"
Cohesion: 0.09
Nodes (3): _sample_chat_response(), test_chat_not_found(), test_chat_success()

### Community 8 - "test_purchase_list.py"
Cohesion: 0.16
Nodes (23): _extract_product_id(), is_purchase_list_query(), is_top_categories_query(), match_rule_intent(), _normalize(), parse_intent_label(), Intent, True when the user asks for a replenishment list or inventory dashboard. (+15 more)

### Community 9 - "AnalyticalScope"
Cohesion: 0.08
Nodes (56): Any, AnalyticalScope, can_export(), effective_scope(), Ask/Agent panel modes — pure helpers for explore vs commit., Filter dimensions (excluding highlight) must match when entering commit., scopes_match_filters(), validate_commit_request() (+48 more)

### Community 10 - "export_catalog_csvs.py"
Cohesion: 0.48
Nodes (6): _as_num(), _as_str(), main(), Path, Split docs/perfumeria_enriched.xlsx into resource-oriented CSVs under data/.…, _write()

### Community 16 - "Traceability matrix — active changes"
Cohesion: 0.13
Nodes (15): dual-surface / metrics, dual-surface / purchase-export, dual-surface / surfaces (API-backed), engineering-quality / deployment, engineering-quality / security, interactive-drilldown / filter_rows, interactive-drilldown / scope, interactive-drilldown / slice-api (+7 more)

### Community 17 - "SupplyMate"
Cohesion: 0.12
Nodes (17): Alcance, Calidad y mantenimiento, Cómo funciona, Docker (API), Documentación / SDD, El flujo (menos de 2 minutos), Flujo en terminal, Inicio rápido (+9 more)

### Community 19 - "components.py"
Cohesion: 0.20
Nodes (7): DataFrame, build_purchase_dataframe(), _kpi_card(), Any, Componentes visuales didácticos para Streamlit., render_kpi_strip(), render_purchase_table()

### Community 21 - "charts.py"
Cohesion: 0.22
Nodes (8): Chart, Scale, Tooltip, histogram(), lollipop(), _qty_color_scale(), Altair charts for SupplyMate drill-down (static + selectable)., Visual theme — colores semánticos para SupplyMate Operación.

### Community 22 - "Requirements"
Cohesion: 0.20
Nodes (9): Charts, Chips, CSV, Empty state, Live panel, Navigation, Requirements, SKU inspection (+1 more)

### Community 23 - "Tasks: engineering-quality"
Cohesion: 0.22
Nodes (8): Phase 0 — SDD, Phase 1 — Traceability audit, Phase 2 — Security (Strict TDD), Phase 3 — CI, Phase 4 — Smoke + performance, Phase 5 — Maintenance + audit docs, Phase 6 — UX + close, Tasks: engineering-quality

### Community 24 - "Proposal: interactive-drilldown"
Cohesion: 0.22
Nodes (8): Capabilities, Non-Goals, Proposal: interactive-drilldown, Risks, Roadmap (later changes, not this one), Rollback, What Changes, Why

### Community 25 - "Protocolo de prueba beta — SupplyMate"
Cohesion: 0.25
Nodes (8): Checklist UX automatizable (manual), Criterio de éxito beta, Duración, Escenario narrativo, Participante, Pasos, Protocolo de prueba beta — SupplyMate, Registro de hallazgos

### Community 26 - "Design: interactive-drilldown"
Cohesion: 0.25
Nodes (7): AnalyticalScope, Data path, Design: interactive-drilldown, Filter semantics, Gotcha, Principle, Streamlit

### Community 27 - "Requirements"
Cohesion: 0.25
Nodes (7): add, AnalyticalScope model, cache_key, filter_rows, remove and reset, Requirements, Spec: scope

### Community 28 - "Tasks: interactive-drilldown"
Cohesion: 0.25
Nodes (7): Phase 0 — SDD, Phase 1 — Scope + filter (Strict TDD), Phase 2 — Evidence + chips (Strict TDD), Phase 3 — API (Strict TDD), Phase 4 — Streamlit (verify), Phase 5 — Ship, Tasks: interactive-drilldown

### Community 29 - "Plantilla — solicitud de cambio"
Cohesion: 0.29
Nodes (7): 1. Resumen, 2. Motivación, 3. Impacto en el sistema, 4. Riesgos, 5. Plan de pruebas, 6. Decisión, Plantilla — solicitud de cambio

### Community 30 - "Design: engineering-quality"
Cohesion: 0.29
Nodes (6): CI layout, Design: engineering-quality, Environment, Performance thresholds, Security middleware stack, Traceability

### Community 31 - "Security spec (OWASP-minimal)"
Cohesion: 0.29
Nodes (6): Dependencies (A06), Error handling (A05), Headers, Input validation (A03), Rate limiting (A07), Security spec (OWASP-minimal)

### Community 32 - "Verify report — engineering-quality"
Cohesion: 0.29
Nodes (6): Coverage (critical modules), Spec coverage, TDD cycle evidence, UX / beta, Verdict, Verify report — engineering-quality

### Community 33 - "Política de mantenimiento — SupplyMate"
Cohesion: 0.33
Nodes (6): Evolución vs servicio, Flujo de cambio, Mantenimiento preventivo (Ley #2), Política de mantenimiento — SupplyMate, Referencias, Tipos de mantenimiento

### Community 34 - "Proposal: engineering-quality"
Cohesion: 0.33
Nodes (5): Non-Goals, Proposal: engineering-quality, Reference, What Changes, Why

### Community 35 - "Requirements"
Cohesion: 0.33
Nodes (5): Aligned endpoints, Data source, GET /replenishment/slice, Requirements, Spec: slice-api

### Community 36 - "Requirements"
Cohesion: 0.33
Nodes (5): Ranking order (first applicable, up to 3), Requirements, Spec: suggested-filters, suggest_next_filters, SuggestedFilter shape

### Community 37 - "Design: natural-query-interpretation"
Cohesion: 0.04
Nodes (47): 1. Código numérico (5+ dígitos), 2. Texto libre, 3. Normalización morfológica, 4. Empates, Alta confianza — replenishment multi-grupo, Baja confianza, `build_scope()`, `BusinessIntent` (+39 more)

### Community 39 - "Perfil operativo — rendimiento"
Cohesion: 0.40
Nodes (4): Mix de carga esperado (MVP), Notas, Perfil operativo — rendimiento, Umbrales smoke (`tests/test_performance.py`)

### Community 40 - "Proposal: llm-drilldown-insights"
Cohesion: 0.40
Nodes (4): Non-Goals, Proposal: llm-drilldown-insights, What Changes, Why

### Community 41 - "Deployment spec"
Cohesion: 0.50
Nodes (3): Deployment spec, Docker, Smoke script

### Community 42 - "Design: llm-drilldown-insights"
Cohesion: 0.50
Nodes (3): Ask / Agent, Design: llm-drilldown-insights, Flow

### Community 50 - "ProductMaster"
Cohesion: 0.12
Nodes (29): ProductMaster, ReplenishmentResult, analytics_rows(), days_of_supply(), estimated_purchase_value(), health_bucket(), metric_prompt_block(), MetricContract (+21 more)

### Community 51 - "interpret_query_rules"
Cohesion: 0.13
Nodes (36): QueryInterpretation, Reference, ResolutionResult, ResolvedReference, _extract_entity_tokens(), _extract_filter_hints(), _has_risk_intent(), interpret_query() (+28 more)

### Community 54 - "ADDED Requirements"
Cohesion: 0.18
Nodes (10): ADDED Requirements, Requirement: Get inventory by product, Requirement: Get replenishment params by product, Requirement: Get sales history by product, Requirement: Unknown product handling, Scenario: Unknown product id, Scenario: Valid product inventory, Scenario: Valid replenishment params (+2 more)

### Community 55 - "ADDED Requirements"
Cohesion: 0.20
Nodes (9): ADDED Requirements, Replenishment Spec, Requirement: Average daily demand, Requirement: Demand components and stock target, Requirement: Recommended order quantity, Scenario: Happy path average, Scenario: Positive order quantity, Scenario: Stock exceeds target (+1 more)

### Community 56 - "ProductNotFoundError"
Cohesion: 0.05
Nodes (64): ProductNotFoundError, clear_product_caches(), _lexical_resolve(), load_products(), message_looks_like_sku(), _normalize(), Path, True when the text contains a catalog-style numeric code (5+ digits). (+56 more)

### Community 57 - "Requirements"
Cohesion: 0.22
Nodes (8): Build, Health view, Materialization, Purpose, Purpose, Regeneration, Requirements, Spec: analytics-db

### Community 58 - "ADDED Requirements"
Cohesion: 0.22
Nodes (8): ADDED Requirements, API Spec, Requirement: Chat endpoint, Requirement: Health endpoint, Requirement: Unknown product error, Scenario: Health check, Scenario: Missing product, Scenario: Successful recommendation

### Community 59 - "Proposal: dual-surface-analytics"
Cohesion: 0.25
Nodes (7): Capabilities, Non-Goals, Proposal: dual-surface-analytics, Risks, Rollback, What Changes, Why

### Community 60 - "Requirements"
Cohesion: 0.25
Nodes (7): Canonical labels, Days of supply, Health bucket, Parity with replenishment, Purpose, Requirements, Spec: metrics

### Community 61 - "Design: mvp-core"
Cohesion: 0.25
Nodes (7): Architecture, Components, Design: mvp-core, Formula, Stack decisions, Testing strategy, Threats (MVP)

### Community 62 - "Proposal: mvp-core"
Cohesion: 0.25
Nodes (7): Capabilities, Non-Goals, Proposal: mvp-core, Risks, Rollback, What Changes, Why

### Community 63 - "Tasks: mvp-core"
Cohesion: 0.25
Nodes (7): Phase 0 — Scaffold, Phase 1 — Replenishment (Strict TDD), Phase 2 — Tools (Strict TDD), Phase 3 — Agent (Strict TDD), Phase 4 — API (Strict TDD), Phase 5 — Ship, Tasks: mvp-core

### Community 64 - "API simulada — contrato de datos SupplyMate"
Cohesion: 0.29
Nodes (6): API simulada — contrato de datos SupplyMate, Diagrama de relación, Recursos, Regenerar desde el dump Excel, Runtime, Variables de entorno

### Community 65 - "Design: dual-surface-analytics"
Cohesion: 0.29
Nodes (6): Anti-patterns avoided, Architecture, Dashboard wire (single), Deep-link, Design: dual-surface-analytics, Product model

### Community 66 - "Requirements"
Cohesion: 0.29
Nodes (6): CSV export, Enriched list item, No product analytics health API, Purpose, Requirements, Spec: purchase-export

### Community 67 - "Tasks: dual-surface-analytics"
Cohesion: 0.29
Nodes (6): Phase 1 — Metrics (Strict TDD), Phase 2 — Analytics DB (Strict TDD), Phase 3 — Purchase export (Strict TDD), Phase 4 — Surfaces, Phase 5 — Verify, Tasks: dual-surface-analytics

### Community 68 - "Verify report — dual-surface-analytics"
Cohesion: 0.29
Nodes (6): pytest, Spec coverage, TDD cycle evidence, UX coherence checklist, Verdict, Verify report — dual-surface-analytics

### Community 69 - "Tasks: semantic-correctness"
Cohesion: 0.29
Nodes (6): Phase 0 — SDD, Phase 1 — Embeddings perimeter, Phase 2 — Policy + metrics, Phase 3 — Evals + logs, Phase 4 — Value + demo, Tasks: semantic-correctness

### Community 70 - "Requirements"
Cohesion: 0.33
Nodes (5): Operation (Streamlit chat), Purpose, Requirements, Shared product identity, Spec: surfaces

### Community 71 - "ADDED Requirements"
Cohesion: 0.33
Nodes (5): ADDED Requirements, Agent Spec, Requirement: Explanation uses calculation, Requirement: Two-phase recommendation flow, Scenario: Quantity comes from Python

### Community 72 - "Verify Report: mvp-core"
Cohesion: 0.33
Nodes (5): Notes, Spec coverage, TDD Cycle Evidence, Verdict, Verify Report: mvp-core

### Community 73 - "Requirements"
Cohesion: 0.33
Nodes (5): Explain fallback, Golden intents, Insight fixtures, Requirements, Spec: llm-evals

### Community 74 - "Requirements"
Cohesion: 0.33
Nodes (5): Cost basis, CSV, Operational priority, Requirements, Spec: purchase-value

### Community 75 - "Matriz de compatibilidad"
Cohesion: 0.40
Nodes (5): API (:8000), Matriz de compatibilidad, Navegador × SO (Streamlit :8501), No probado formalmente, Regresión manual sugerida

### Community 76 - "Verify report — catalog-integration"
Cohesion: 0.40
Nodes (4): Checks, Demo SKUs, Scope, Verify report — catalog-integration

### Community 77 - "Design: semantic-correctness"
Cohesion: 0.40
Nodes (4): Design: semantic-correctness, LLM vs Python, Logs, Policy

### Community 78 - "Proposal: semantic-correctness"
Cohesion: 0.40
Nodes (4): Non-Goals, Proposal: semantic-correctness, What Changes, Why

### Community 79 - "Requirements"
Cohesion: 0.40
Nodes (4): Declared UI chart dep, No semantic resolve, Requirements, Spec: embeddings-perimeter

### Community 80 - "Requirements"
Cohesion: 0.40
Nodes (4): Canonical caveats, Reorder point display, Requirements, Spec: metric-contracts

### Community 81 - "Requirements"
Cohesion: 0.40
Nodes (4): Fractional remainder, Order-up-to quantity, Requirements, Spec: replenishment-policy

### Community 82 - "Verify report — semantic-correctness"
Cohesion: 0.40
Nodes (4): Spec coverage, TDD / CI, Verdict, Verify report — semantic-correctness

### Community 83 - "Skill Registry"
Cohesion: 0.50
Nodes (3): Indexed skills (paths only), Project conventions, Skill Registry

### Community 84 - "Catalog integration — extends mvp-core with unified master + REST"
Cohesion: 0.50
Nodes (3): Catalog integration — extends mvp-core with unified master + REST, Goal, Tasks

### Community 87 - "Tasks: natural-query-interpretation"
Cohesion: 0.25
Nodes (7): Phase 0 — SDD, Phase 1 — Un grupo + scope en chat (MVP), Phase 2 — Multi-grupo comparativo, Phase 3 — inventory_risk sobre grupos, Phase 4 — Desambiguación, Tasks: natural-query-interpretation, Verify

### Community 90 - "Proposal: natural-query-interpretation"
Cohesion: 0.33
Nodes (5): Non-Goals, Proposal: natural-query-interpretation, Success Criteria, What Changes, Why

### Community 94 - "SecurityHeadersMiddleware"
Cohesion: 0.29
Nodes (5): BaseHTTPMiddleware, Request, Response, Security response headers., SecurityHeadersMiddleware

### Community 95 - "Verify report — interactive-drilldown"
Cohesion: 0.33
Nodes (6): Spec coverage, TDD cycle evidence, Traceability, UX checklist (5 min manual), Verdict, Verify report — interactive-drilldown

### Community 96 - "Verify: natural-query-interpretation"
Cohesion: 0.33
Nodes (5): API checks, Manual smoke (recommended), Non-goals confirmed, pytest, Verify: natural-query-interpretation

## Knowledge Gaps
- **316 isolated node(s):** `Phase 0 — SDD`, `Phase 1 — Un grupo + scope en chat (MVP)`, `Phase 2 — Multi-grupo comparativo`, `Phase 3 — inventory_risk sobre grupos`, `Phase 4 — Desambiguación` (+311 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 498 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AnalyticalScope` connect `AnalyticalScope` to `dashboard.py`, `agent.py`, `models.py`, `test_analyze_api.py`, `interpret_query_rules`, `ProductNotFoundError`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `run_supplymate()` connect `agent.py` to `test_purchase_list.py`, `ProductNotFoundError`, `interpret_query_rules`, `models.py`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Why does `ProductMaster` connect `ProductMaster` to `ProductNotFoundError`, `dashboard.py`, `store.py`, `models.py`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Are the 31 inferred relationships involving `AnalyticalScope` (e.g. with `_run_explore()` and `inventory_dashboard()`) actually correct?**
  _`AnalyticalScope` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `ProductNotFoundError` (e.g. with `chat()` and `get_product()`) actually correct?**
  _`ProductNotFoundError` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `run_analyze()` (e.g. with `AnalyzeRequest` and `CommitSummary`) actually correct?**
  _`run_analyze()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Phase 0 — SDD`, `Phase 1 — Un grupo + scope en chat (MVP)`, `Phase 2 — Multi-grupo comparativo` to the rest of the system?**
  _316 weakly-connected nodes found - possible documentation gaps or missing edges._