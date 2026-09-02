# Graph Report - SupplyMate  (2026-09-02)

## Corpus Check
- 145 files · ~56,294 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1164 nodes · 2546 edges · 99 communities (85 shown, 9 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 186 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d051a53b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- products.py
- dashboard.py
- run_supplymate
- api.py
- models.py
- config.py
- bug_report.md
- test_api.py
- is_purchase_list_query
- AnalyticalScope
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
- guidance.py
- store.py
- reference_resolver.py
- catalog_service.py
- ADDED Requirements
- ADDED Requirements
- test_tools.py
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
- calculate_replenishment
- Tasks: natural-query-interpretation
- get_replenishment_recommendation
- test_security.py
- Proposal: natural-query-interpretation
- BaseModel
- test_analyze_api.py
- _run_explore
- SecurityHeadersMiddleware
- Verify report — interactive-drilldown
- Verify: natural-query-interpretation
- ProductNotFoundError
- safe_errors.py

## God Nodes (most connected - your core abstractions)
1. `AnalyticalScope` - 126 edges
2. `run_supplymate()` - 53 edges
3. `get_store()` - 34 edges
4. `ProductNotFoundError` - 29 edges
5. `run_analyze()` - 28 edges
6. `ProductMaster` - 28 edges
7. `PurchaseListItem` - 27 edges
8. `interpret_query_rules()` - 26 edges
9. `InventoryDashboard` - 25 edges
10. `normalize_text()` - 24 edges

## Surprising Connections (you probably didn't know these)
- `apply_guidance_chip_action()` --uses--> `GuidanceChip`  [INFERRED]
  ui/streamlit_app.py → app/models.py
- `test_run_analyze_priorities_subset_of_purchase_list()` --uses--> `AnalyticalScope`  [INFERRED]
  tests/test_agent.py → app/models.py
- `test_analyze_commit_requires_frozen_scope()` --calls--> `AnalyticalScope`  [EXTRACTED]
  tests/test_analyze_api.py → app/models.py
- `test_analyze_invalid_llm_json_fallback()` --calls--> `AnalyticalScope`  [EXTRACTED]
  tests/test_analyze_api.py → app/models.py
- `test_mamaderas_union_is_small_group()` --uses--> `AnalyticalScope`  [INFERRED]
  tests/test_guidance_plan.py → app/models.py

## Import Cycles
- None detected.

## Communities (99 total, 9 thin omitted)

### Community 0 - "products.py"
Cohesion: 0.24
Nodes (12): clear_product_caches(), _lexical_resolve(), load_products(), _normalize(), Path, Extract a product reference from a natural-language message., Resolve free-text to product_id: catalog code, barcode, or name., resolve_from_message() (+4 more)

### Community 1 - "dashboard.py"
Cohesion: 0.17
Nodes (23): CategorySalesBar, coverage_bucket(), filter_rows(), from_rows(), purchase_items(), Inventory dashboard for the Streamlit chat — same metrics as Python…, _row_category(), _row_subcategory() (+15 more)

### Community 2 - "run_supplymate"
Cohesion: 0.27
Nodes (18): Route by interpreted intent + catalog resolution, then deterministic Python., run_supplymate(), asyncio, test_explain_orphan_falls_back_to_deterministic_text(), test_fallback_hydrates_when_agent_skips_tools(), test_llm_classifies_sales_paraphrase(), test_llm_classifies_stockout_paraphrase_as_purchase_list(), test_llm_unknown_does_not_force_a_random_sku() (+10 more)

### Community 3 - "api.py"
Cohesion: 0.19
Nodes (17): get_product(), get_replenishment(), health(), inventory_dashboard(), purchase_list(), purchase_list_csv(), Response, replenishment_slice() (+9 more)

### Community 4 - "models.py"
Cohesion: 0.09
Nodes (51): _run_purchase_list(), CategoryBar, CommitSummary, CoverageBar, DashboardInsight, InteractionEvent, InventoryDashboard, PurchaseListItem (+43 more)

### Community 5 - "config.py"
Cohesion: 0.23
Nodes (10): effective_analyze_rate_limit(), effective_chat_rate_limit(), is_test_env(), ChatRateLimitMiddleware, BaseHTTPMiddleware, Request, Response, Rate limit POST /chat and POST /replenishment/analyze by client IP. (+2 more)

### Community 6 - "bug_report.md"
Cohesion: 0.11
Nodes (16): Auditoría OSSTMM lite — Sección C (Internet), C — Seguridad en tecnologías de Internet, Fuera de alcance (OSSTMM D–F), Próximos pasos (producción), Actualización, Auditoría local, Dependencias y auditoría (OWASP A06), Pinning (+8 more)

### Community 7 - "test_api.py"
Cohesion: 0.09
Nodes (3): ChatResponse, _sample_chat_response(), test_chat_success()

### Community 8 - "is_purchase_list_query"
Cohesion: 0.16
Nodes (22): is_purchase_list_query(), is_top_categories_query(), match_rule_intent(), _normalize(), parse_intent_label(), Intent, True when the user asks for a replenishment list or inventory dashboard., Cheap regex router. None means the concept was not recognized. (+14 more)

### Community 9 - "AnalyticalScope"
Cohesion: 0.08
Nodes (60): AnalyticalScope, can_export(), effective_scope(), PanelMode, Ask/Agent panel modes — pure helpers for explore vs commit., Filter dimensions (excluding highlight) must match when entering commit., scopes_match_filters(), validate_commit_request() (+52 more)

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
Cohesion: 0.17
Nodes (24): build_commit_agent(), build_explain_agent(), build_insight_agent(), build_supply_agent(), _extract_product_id(), _fallback_analyze_response(), get_model(), _parse_json_output() (+16 more)

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

### Community 48 - "guidance.py"
Cohesion: 0.09
Nodes (53): _labels_from_scope(), run_apply_chip(), _chip_for_mission(), apply_guidance_chip(), chip_for_draft_oc(), chip_for_name_token(), chip_for_stockout(), chip_for_subcategory() (+45 more)

### Community 50 - "store.py"
Cohesion: 0.08
Nodes (47): ProductMaster, ReplenishmentResult, analytics_rows(), days_of_supply(), estimated_purchase_value(), health_bucket(), metric_prompt_block(), MetricContract (+39 more)

### Community 51 - "reference_resolver.py"
Cohesion: 0.08
Nodes (64): QueryInterpretation, Reference, ResolutionResult, ResolvedReference, message_looks_like_sku(), True when the text contains a catalog-style numeric code (5+ digits)., classify_relation(), _extract_entity_tokens() (+56 more)

### Community 52 - "catalog_service.py"
Cohesion: 0.13
Nodes (23): _run_top_categories(), ProductContext, ReplenishmentRecommendation, chat_dashboard(), format_purchase_list_answer(), format_sales_answer(), format_single_product_answer(), format_slice_evidence() (+15 more)

### Community 54 - "ADDED Requirements"
Cohesion: 0.18
Nodes (10): ADDED Requirements, Requirement: Get inventory by product, Requirement: Get replenishment params by product, Requirement: Get sales history by product, Requirement: Unknown product handling, Scenario: Unknown product id, Scenario: Valid product inventory, Scenario: Valid replenishment params (+2 more)

### Community 55 - "ADDED Requirements"
Cohesion: 0.20
Nodes (9): ADDED Requirements, Replenishment Spec, Requirement: Average daily demand, Requirement: Demand components and stock target, Requirement: Recommended order quantity, Scenario: Happy path average, Scenario: Positive order quantity, Scenario: Stock exceeds target (+1 more)

### Community 56 - "test_tools.py"
Cohesion: 0.12
Nodes (27): _hydrate_context(), SupplyContext, resolve_product(), get_inventory(), get_replenishment_params(), get_sales_history(), load_inventory(), load_replenishment_params() (+19 more)

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
Cohesion: 0.20
Nodes (12): build_classifier_agent(), classify_intent(), Agent, Intent, LLM concept router. None = classifier unavailable; caller should fall back., emit(), Any, Minimal JSON logs for LLM runner calls. No prompt bodies. (+4 more)

### Community 86 - "calculate_replenishment"
Cohesion: 0.19
Nodes (12): calculate_replenishment(), Catalog IDs used across tests (must exist in data/)., test_average_daily_demand_from_30_day_total(), test_ceil_rounds_fractional_gap_up(), test_different_lead_time_triangulation(), test_policy_does_not_use_reorder_point(), test_recommended_quantity_zero_when_stock_exceeds_target(), test_stock_target_components() (+4 more)

### Community 87 - "Tasks: natural-query-interpretation"
Cohesion: 0.25
Nodes (7): Phase 0 — SDD, Phase 1 — Un grupo + scope en chat (MVP), Phase 2 — Multi-grupo comparativo, Phase 3 — inventory_risk sobre grupos, Phase 4 — Desambiguación, Tasks: natural-query-interpretation, Verify

### Community 88 - "get_replenishment_recommendation"
Cohesion: 0.24
Nodes (12): get_master(), get_replenishment_by_query(), get_replenishment_recommendation(), test_formula_parity(), test_get_master(), test_get_replenishment_by_query(), test_recommendation_context_prices(), test_replenishment_recommendation_high_qty() (+4 more)

### Community 89 - "test_security.py"
Cohesion: 0.24
Nodes (7): reset_rate_limits(), test_analyze_rate_limit_429(), _clean_rate_limits(), _minimal_chat(), fixture, test_chat_rate_limit_returns_429(), test_health_not_rate_limited()

### Community 90 - "Proposal: natural-query-interpretation"
Cohesion: 0.33
Nodes (5): Non-Goals, Proposal: natural-query-interpretation, Success Criteria, What Changes, Why

### Community 91 - "BaseModel"
Cohesion: 0.39
Nodes (8): ChatRequest, Inventory, ReplenishmentParams, SaleRecord, SalesHistory, BaseModel, _seed_context_for_high_qty(), test_run_supplymate_zero_quantity_triangulation()

### Community 92 - "test_analyze_api.py"
Cohesion: 0.31
Nodes (8): _clean(), _commit_payload(), _insight_payload(), fixture, test_analyze_commit_requires_frozen_scope(), test_analyze_commit_with_frozen_scope(), test_analyze_explore_returns_200(), test_analyze_invalid_llm_json_fallback()

### Community 93 - "_run_explore"
Cohesion: 0.43
Nodes (7): _run_disambiguation(), _run_explore(), format_disambiguation_answer(), format_explore_answer(), group_summaries_from_resolved(), ChatInterpretation, GroupSummary

### Community 94 - "SecurityHeadersMiddleware"
Cohesion: 0.29
Nodes (5): BaseHTTPMiddleware, Request, Response, Security response headers., SecurityHeadersMiddleware

### Community 95 - "Verify report — interactive-drilldown"
Cohesion: 0.33
Nodes (6): Spec coverage, TDD cycle evidence, Traceability, UX checklist (5 min manual), Verdict, Verify report — interactive-drilldown

### Community 96 - "Verify: natural-query-interpretation"
Cohesion: 0.33
Nodes (5): API checks, Manual smoke (recommended), Non-goals confirmed, pytest, Verify: natural-query-interpretation

### Community 97 - "ProductNotFoundError"
Cohesion: 0.25
Nodes (7): chat(), ProductNotFoundError, safe_resolve(), Exception, post, test_chat_not_found(), test_safe_resolve_unknown()

### Community 98 - "safe_errors.py"
Cohesion: 0.29
Nodes (6): is_production(), BaseHTTPMiddleware, Request, Response, Catch unhandled errors; hide details in production., SafeErrorMiddleware

## Knowledge Gaps
- **316 isolated node(s):** `C:\Users\Equipo\.local\bin\graphify.exe`, `MetricContract`, `supplymate`, `smoke_api.sh script`, `Project conventions` (+311 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 504 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AnalyticalScope` connect `AnalyticalScope` to `dashboard.py`, `run_supplymate`, `api.py`, `models.py`, `guidance.py`, `agent.py`, `reference_resolver.py`, `catalog_service.py`, `get_replenishment_recommendation`, `test_security.py`, `BaseModel`, `test_analyze_api.py`, `_run_explore`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Why does `ProductMaster` connect `store.py` to `dashboard.py`, `api.py`, `models.py`, `catalog_service.py`, `get_replenishment_recommendation`, `BaseModel`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Why does `run_supplymate()` connect `run_supplymate` to `ProductNotFoundError`, `api.py`, `models.py`, `test_api.py`, `is_purchase_list_query`, `AnalyticalScope`, `guidance.py`, `agent.py`, `reference_resolver.py`, `catalog_service.py`, `classify_intent`, `BaseModel`, `_run_explore`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Are the 52 inferred relationships involving `AnalyticalScope` (e.g. with `_labels_from_scope()` and `run_apply_chip()`) actually correct?**
  _`AnalyticalScope` has 52 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `run_supplymate()` (e.g. with `ChatResponse` and `GuidanceChip`) actually correct?**
  _`run_supplymate()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `ProductNotFoundError` (e.g. with `chat()` and `get_product()`) actually correct?**
  _`ProductNotFoundError` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `C:\Users\Equipo\.local\bin\graphify.exe`, `MetricContract`, `supplymate` to the rest of the system?**
  _316 weakly-connected nodes found - possible documentation gaps or missing edges._