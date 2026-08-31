# Graph Report - SupplyMate  (2026-08-31)

## Corpus Check
- 133 files · ~35,322 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1076 nodes · 2136 edges · 97 communities (83 shown, 9 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 136 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `61e1cd49`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_tools.py
- dashboard.py
- run_supplymate
- store.py
- insight_validator.py
- config.py
- bug_report.md
- test_api.py
- is_purchase_list_query
- streamlit_app.py
- export_catalog_csvs.py
- app/__init__.py
- supplymate
- graphify
- Traceability matrix — active changes
- SupplyMate
- agent.py
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
- get_inventory
- ProductMaster
- reference_resolver.py
- run_analyze
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
- classify_intent
- catalog_service.py
- Tasks: natural-query-interpretation
- api.py
- InventoryDashboard
- Proposal: natural-query-interpretation
- models.py
- AnalyticalScope
- test_security.py
- SecurityHeadersMiddleware
- Verify report — interactive-drilldown
- Verify: natural-query-interpretation

## God Nodes (most connected - your core abstractions)
1. `AnalyticalScope` - 86 edges
2. `run_supplymate()` - 35 edges
3. `ProductNotFoundError` - 29 edges
4. `run_analyze()` - 28 edges
5. `ProductMaster` - 28 edges
6. `get_store()` - 24 edges
7. `PurchaseListItem` - 22 edges
8. `calculate_replenishment()` - 22 edges
9. `get_replenishment_recommendation()` - 22 edges
10. `CatalogStore` - 22 edges

## Surprising Connections (you probably didn't know these)
- `test_run_analyze_priorities_subset_of_purchase_list()` --uses--> `AnalyticalScope`  [INFERRED]
  tests/test_agent.py → app/models.py
- `_analyze_cache_key()` --uses--> `AnalyticalScope`  [INFERRED]
  ui/streamlit_app.py → app/models.py
- `_breadcrumb_labels()` --uses--> `AnalyticalScope`  [INFERRED]
  ui/streamlit_app.py → app/models.py
- `_effective_panel_scope()` --uses--> `AnalyticalScope`  [INFERRED]
  ui/streamlit_app.py → app/models.py
- `fetch_analyze()` --uses--> `AnalyticalScope`  [INFERRED]
  ui/streamlit_app.py → app/models.py

## Import Cycles
- None detected.

## Communities (97 total, 9 thin omitted)

### Community 0 - "test_tools.py"
Cohesion: 0.19
Nodes (15): get_sales_history(), date, resolve_product(), load_inventory(), load_replenishment_params(), load_sales_history(), date, Path (+7 more)

### Community 1 - "dashboard.py"
Cohesion: 0.17
Nodes (23): CategorySalesBar, coverage_bucket(), filter_rows(), from_rows(), purchase_items(), Inventory dashboard for the Streamlit chat — same metrics as Python…, _row_category(), _row_subcategory() (+15 more)

### Community 2 - "run_supplymate"
Cohesion: 0.14
Nodes (34): Route by interpreted intent + catalog resolution, then deterministic Python., _run_disambiguation(), _run_explore(), _run_purchase_list(), run_supplymate(), _run_top_categories(), format_disambiguation_answer(), format_explore_answer() (+26 more)

### Community 3 - "store.py"
Cohesion: 0.14
Nodes (23): _as_float(), _as_int(), _as_str(), _build_master(), CatalogStore, _expand_sales(), get_store(), _index_barcodes() (+15 more)

### Community 4 - "insight_validator.py"
Cohesion: 0.20
Nodes (24): CommitSummary, DashboardInsight, PurchasePriority, ReplenishmentSlice, _add_number(), _allowed_numbers(), allowed_numbers_from_mapping(), _items_by_id() (+16 more)

### Community 5 - "config.py"
Cohesion: 0.15
Nodes (15): effective_analyze_rate_limit(), effective_chat_rate_limit(), is_production(), is_test_env(), ChatRateLimitMiddleware, BaseHTTPMiddleware, Request, Response (+7 more)

### Community 6 - "bug_report.md"
Cohesion: 0.11
Nodes (16): Auditoría OSSTMM lite — Sección C (Internet), C — Seguridad en tecnologías de Internet, Fuera de alcance (OSSTMM D–F), Próximos pasos (producción), Actualización, Auditoría local, Dependencias y auditoría (OWASP A06), Pinning (+8 more)

### Community 7 - "test_api.py"
Cohesion: 0.08
Nodes (4): Catalog IDs used across tests (must exist in data/)., _sample_chat_response(), test_chat_not_found(), test_chat_success()

### Community 8 - "is_purchase_list_query"
Cohesion: 0.19
Nodes (19): is_purchase_list_query(), is_top_categories_query(), match_rule_intent(), _normalize(), parse_intent_label(), Intent, True when the user asks for a replenishment list or inventory dashboard., Cheap regex router. None means the concept was not recognized. (+11 more)

### Community 9 - "streamlit_app.py"
Cohesion: 0.10
Nodes (43): InteractionEvent, add(), cache_key(), clear_highlight(), empty_scope(), Analytical scope: deterministic drill-down filters., remove(), reset() (+35 more)

### Community 10 - "export_catalog_csvs.py"
Cohesion: 0.48
Nodes (6): _as_num(), _as_str(), main(), Path, Split docs/perfumeria_enriched.xlsx into resource-oriented CSVs under data/.…, _write()

### Community 16 - "Traceability matrix — active changes"
Cohesion: 0.13
Nodes (15): dual-surface / metrics, dual-surface / purchase-export, dual-surface / surfaces (API-backed), engineering-quality / deployment, engineering-quality / security, interactive-drilldown / filter_rows, interactive-drilldown / scope, interactive-drilldown / slice-api (+7 more)

### Community 17 - "SupplyMate"
Cohesion: 0.12
Nodes (17): Alcance, Calidad y mantenimiento, Cómo funciona, Docker (API), Documentación / SDD, El flujo (menos de 2 minutos), Flujo en terminal, Inicio rápido (+9 more)

### Community 18 - "agent.py"
Cohesion: 0.20
Nodes (16): build_commit_agent(), build_explain_agent(), build_insight_agent(), build_supply_agent(), _extract_product_id(), get_model(), _hydrate_context(), Agent (+8 more)

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

### Community 48 - "get_inventory"
Cohesion: 0.33
Nodes (9): get_inventory(), get_replenishment_params(), get_sales_history(), Any, Return current stock. product_id may be a code, barcode, or name fragment., Return recent sales. product_id may be a code, barcode, or product name., Return lead_time_days and safety_stock. Accepts code, barcode, or name., function_tool (+1 more)

### Community 50 - "ProductMaster"
Cohesion: 0.09
Nodes (40): get_product(), ProductMaster, ReplenishmentResult, calculate_replenishment(), get_master(), analytics_rows(), days_of_supply(), estimated_purchase_value() (+32 more)

### Community 51 - "reference_resolver.py"
Cohesion: 0.12
Nodes (38): QueryInterpretation, Reference, ResolutionResult, ResolvedReference, message_looks_like_sku(), True when the text contains a catalog-style numeric code (5+ digits)., _extract_entity_tokens(), _extract_filter_hints() (+30 more)

### Community 52 - "run_analyze"
Cohesion: 0.11
Nodes (27): _fallback_analyze_response(), _parse_json_output(), run_analyze(), replenishment_analyze(), AnalyzeRequest, AnalyzeResponse, cache_key(), events_hash() (+19 more)

### Community 54 - "ADDED Requirements"
Cohesion: 0.18
Nodes (10): ADDED Requirements, Requirement: Get inventory by product, Requirement: Get replenishment params by product, Requirement: Get sales history by product, Requirement: Unknown product handling, Scenario: Unknown product id, Scenario: Valid product inventory, Scenario: Valid replenishment params (+2 more)

### Community 55 - "ADDED Requirements"
Cohesion: 0.20
Nodes (9): ADDED Requirements, Replenishment Spec, Requirement: Average daily demand, Requirement: Demand components and stock target, Requirement: Recommended order quantity, Scenario: Happy path average, Scenario: Positive order quantity, Scenario: Stock exceeds target (+1 more)

### Community 56 - "ProductNotFoundError"
Cohesion: 0.16
Nodes (17): ProductNotFoundError, clear_product_caches(), _lexical_resolve(), load_products(), _normalize(), Path, Extract a product reference from a natural-language message., Resolve free-text to product_id: catalog code, barcode, or name. (+9 more)

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

### Community 85 - "classify_intent"
Cohesion: 0.21
Nodes (11): build_classifier_agent(), classify_intent(), Agent, Intent, LLM concept router. None = classifier unavailable; caller should fall back., llm, asyncio, test_groq_classifies_hard_intents() (+3 more)

### Community 86 - "catalog_service.py"
Cohesion: 0.11
Nodes (27): PurchaseListItem, chat_dashboard(), format_dashboard_answer(), format_purchase_list_answer(), format_sales_answer(), format_single_product_answer(), format_slice_evidence(), get_replenishment_by_query() (+19 more)

### Community 87 - "Tasks: natural-query-interpretation"
Cohesion: 0.25
Nodes (7): Phase 0 — SDD, Phase 1 — Un grupo + scope en chat (MVP), Phase 2 — Multi-grupo comparativo, Phase 3 — inventory_risk sobre grupos, Phase 4 — Desambiguación, Tasks: natural-query-interpretation, Verify

### Community 88 - "api.py"
Cohesion: 0.17
Nodes (17): chat(), get_replenishment(), health(), inventory_dashboard(), purchase_list(), purchase_list_csv(), Response, _scope_dependency() (+9 more)

### Community 89 - "InventoryDashboard"
Cohesion: 0.23
Nodes (13): InventoryDashboard, metric_prompt_block(), compile_analyze_prompt(), _dashboard_summary(), _delta_vs_root(), _event_line(), prompt_hash(), _purchase_top() (+5 more)

### Community 90 - "Proposal: natural-query-interpretation"
Cohesion: 0.33
Nodes (5): Non-Goals, Proposal: natural-query-interpretation, Success Criteria, What Changes, Why

### Community 91 - "models.py"
Cohesion: 0.22
Nodes (16): CategoryBar, ChatRequest, CoverageBar, ProductContext, ProductSearchHit, ReplenishmentRecommendation, SuggestedFilter, Deterministic suggested filter chips from slice data (no LLM). (+8 more)

### Community 92 - "AnalyticalScope"
Cohesion: 0.22
Nodes (15): replenishment_slice(), In-memory rate limiter for POST /chat., reset_rate_limits(), AnalyticalScope, replenishment_slice(), _commit_payload(), _insight_payload(), test_analyze_commit_requires_frozen_scope() (+7 more)

### Community 93 - "test_security.py"
Cohesion: 0.24
Nodes (5): _clean_rate_limits(), _minimal_chat(), fixture, test_chat_rate_limit_returns_429(), test_health_not_rate_limited()

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
- **316 isolated node(s):** `C:\Users\Equipo\.local\bin\graphify.exe`, `MetricContract`, `supplymate`, `smoke_api.sh script`, `Project conventions` (+311 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 492 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AnalyticalScope` connect `AnalyticalScope` to `dashboard.py`, `run_supplymate`, `streamlit_app.py`, `agent.py`, `reference_resolver.py`, `run_analyze`, `catalog_service.py`, `api.py`, `InventoryDashboard`, `models.py`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `ProductNotFoundError` connect `ProductNotFoundError` to `test_tools.py`, `run_supplymate`, `store.py`, `test_api.py`, `agent.py`, `ProductMaster`, `catalog_service.py`, `api.py`, `models.py`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Why does `classify_intent()` connect `classify_intent` to `is_purchase_list_query`, `agent.py`, `run_supplymate`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Are the 31 inferred relationships involving `AnalyticalScope` (e.g. with `_run_explore()` and `inventory_dashboard()`) actually correct?**
  _`AnalyticalScope` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `ProductNotFoundError` (e.g. with `chat()` and `get_product()`) actually correct?**
  _`ProductNotFoundError` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `run_analyze()` (e.g. with `AnalyzeRequest` and `CommitSummary`) actually correct?**
  _`run_analyze()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `C:\Users\Equipo\.local\bin\graphify.exe`, `MetricContract`, `supplymate` to the rest of the system?**
  _316 weakly-connected nodes found - possible documentation gaps or missing edges._