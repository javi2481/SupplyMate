# Graph Report - SupplyMate  (2026-09-02)

## Corpus Check
- 152 files · ~57,944 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1214 nodes · 2744 edges · 99 communities (85 shown, 9 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 193 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `127729f5`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- dashboard.py
- run_supplymate
- agent.py
- AnalyticalScope
- catalog_service.py
- test_security.py
- bug_report.md
- test_api.py
- products.py
- streamlit_app.py
- export_catalog_csvs.py
- app/__init__.py
- supplymate
- graphify
- Traceability matrix — active changes
- SupplyMate
- insight_validator.py
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
- test_guidance_plan.py
- store.py
- reference_resolver.py
- api.py
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
- prompt_compiler.py
- models.py
- Tasks: natural-query-interpretation
- config.py
- InventoryDashboard
- Proposal: natural-query-interpretation
- safe_errors.py
- get_replenishment_recommendation
- test_analyze_api.py
- SecurityHeadersMiddleware
- Verify report — interactive-drilldown
- Verify: natural-query-interpretation
- SupplyContext
- test_api_contract.py

## God Nodes (most connected - your core abstractions)
1. `AnalyticalScope` - 147 edges
2. `run_supplymate()` - 55 edges
3. `interpret_query_rules()` - 38 edges
4. `get_store()` - 36 edges
5. `ProductNotFoundError` - 29 edges
6. `run_analyze()` - 28 edges
7. `ProductMaster` - 28 edges
8. `replenishment_slice()` - 28 edges
9. `PurchaseListItem` - 27 edges
10. `calculate_replenishment()` - 27 edges

## Surprising Connections (you probably didn't know these)
- `apply_guidance_chip_action()` --uses--> `GuidanceChip`  [INFERRED]
  ui/streamlit_app.py → app/models.py
- `test_run_supplymate_zero_quantity_triangulation()` --uses--> `Inventory`  [INFERRED]
  tests/test_agent.py → app/models.py
- `test_run_supplymate_zero_quantity_triangulation()` --uses--> `SalesHistory`  [INFERRED]
  tests/test_agent.py → app/models.py
- `test_run_analyze_priorities_subset_of_purchase_list()` --uses--> `AnalyticalScope`  [INFERRED]
  tests/test_agent.py → app/models.py
- `test_analyze_commit_requires_frozen_scope()` --calls--> `AnalyticalScope`  [EXTRACTED]
  tests/test_analyze_api.py → app/models.py

## Import Cycles
- None detected.

## Communities (99 total, 9 thin omitted)

### Community 0 - "dashboard.py"
Cohesion: 0.17
Nodes (21): coverage_bucket(), filter_rows(), purchase_items(), Inventory dashboard for the Streamlit chat — same metrics as Python…, _row_category(), _row_subcategory(), total_recommended_qty(), Inventory dashboard aggregates for the chat (no Superset). (+13 more)

### Community 1 - "run_supplymate"
Cohesion: 0.18
Nodes (25): Route by interpreted intent + catalog resolution, then deterministic Python., _run_purchase_list(), run_supplymate(), _run_top_categories(), chat(), ChatResponse, asyncio, test_explain_orphan_falls_back_to_deterministic_text() (+17 more)

### Community 2 - "agent.py"
Cohesion: 0.05
Nodes (67): build_commit_agent(), build_explain_agent(), build_insight_agent(), build_supply_agent(), _extract_product_id(), _fallback_analyze_response(), get_model(), _hydrate_context() (+59 more)

### Community 3 - "AnalyticalScope"
Cohesion: 0.11
Nodes (50): AnalyticalScope, QueryInterpretation, ResolvedReference, message_looks_like_sku(), True when the text contains a catalog-style numeric code (5+ digits)., classify_relation(), _extract_entity_tokens(), _extract_filter_hints() (+42 more)

### Community 4 - "catalog_service.py"
Cohesion: 0.11
Nodes (31): PurchaseListItem, ReplenishmentRecommendation, chat_dashboard(), format_dashboard_answer(), format_purchase_list_answer(), format_sales_answer(), format_single_product_answer(), format_slice_evidence() (+23 more)

### Community 5 - "test_security.py"
Cohesion: 0.23
Nodes (7): In-memory rate limiter for POST /chat., reset_rate_limits(), _clean_rate_limits(), _minimal_chat(), fixture, test_chat_rate_limit_returns_429(), test_health_not_rate_limited()

### Community 6 - "bug_report.md"
Cohesion: 0.11
Nodes (16): Auditoría OSSTMM lite — Sección C (Internet), C — Seguridad en tecnologías de Internet, Fuera de alcance (OSSTMM D–F), Próximos pasos (producción), Actualización, Auditoría local, Dependencias y auditoría (OWASP A06), Pinning (+8 more)

### Community 7 - "test_api.py"
Cohesion: 0.09
Nodes (3): Catalog IDs used across tests (must exist in data/)., _sample_chat_response(), test_chat_success()

### Community 8 - "products.py"
Cohesion: 0.11
Nodes (31): is_purchase_list_query(), is_top_categories_query(), match_rule_intent(), _normalize(), parse_intent_label(), Intent, True when the user asks for a replenishment list or inventory dashboard., Cheap regex router. None means the concept was not recognized. (+23 more)

### Community 9 - "streamlit_app.py"
Cohesion: 0.09
Nodes (52): add(), cache_key(), clear_highlight(), dismiss_guidance(), empty_scope(), Analytical scope: deterministic drill-down filters., remove(), reset() (+44 more)

### Community 10 - "export_catalog_csvs.py"
Cohesion: 0.48
Nodes (6): _as_num(), _as_str(), main(), Path, Split docs/perfumeria_enriched.xlsx into resource-oriented CSVs under data/.…, _write()

### Community 16 - "Traceability matrix — active changes"
Cohesion: 0.13
Nodes (15): dual-surface / metrics, dual-surface / purchase-export, dual-surface / surfaces (API-backed), engineering-quality / deployment, engineering-quality / security, interactive-drilldown / filter_rows, interactive-drilldown / scope, interactive-drilldown / slice-api (+7 more)

### Community 17 - "SupplyMate"
Cohesion: 0.12
Nodes (17): Alcance, Calidad y mantenimiento, Cómo funciona, Docker (API), Documentación / SDD, El flujo (menos de 2 minutos), Flujo en terminal, Inicio rápido (+9 more)

### Community 18 - "insight_validator.py"
Cohesion: 0.20
Nodes (24): CommitSummary, DashboardInsight, PurchasePriority, ReplenishmentSlice, _add_number(), _allowed_numbers(), allowed_numbers_from_mapping(), _items_by_id() (+16 more)

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

### Community 48 - "test_guidance_plan.py"
Cohesion: 0.09
Nodes (54): _labels_from_scope(), run_apply_chip(), _chip_for_mission(), apply_guidance_chip(), chip_for_draft_oc(), chip_for_name_token(), chip_for_stockout(), chip_for_subcategory() (+46 more)

### Community 50 - "store.py"
Cohesion: 0.07
Nodes (47): ProductMaster, ReplenishmentResult, analytics_rows(), days_of_supply(), estimated_purchase_value(), health_bucket(), metric_prompt_block(), MetricContract (+39 more)

### Community 51 - "reference_resolver.py"
Cohesion: 0.09
Nodes (48): is_valid_guidance_option(), Shared size-token helpers for guidance (no imports from guidance.py)., size_tokens_from_skus(), Reference, disambiguation_options(), _display_token(), _group_from_name_hits(), _label_for_group() (+40 more)

### Community 52 - "api.py"
Cohesion: 0.21
Nodes (15): get_product(), get_replenishment(), health(), inventory_dashboard(), purchase_list(), purchase_list_csv(), Response, replenishment_slice() (+7 more)

### Community 54 - "ADDED Requirements"
Cohesion: 0.18
Nodes (10): ADDED Requirements, Requirement: Get inventory by product, Requirement: Get replenishment params by product, Requirement: Get sales history by product, Requirement: Unknown product handling, Scenario: Unknown product id, Scenario: Valid product inventory, Scenario: Valid replenishment params (+2 more)

### Community 55 - "ADDED Requirements"
Cohesion: 0.20
Nodes (9): ADDED Requirements, Replenishment Spec, Requirement: Average daily demand, Requirement: Demand components and stock target, Requirement: Recommended order quantity, Scenario: Happy path average, Scenario: Positive order quantity, Scenario: Stock exceeds target (+1 more)

### Community 56 - "ProductNotFoundError"
Cohesion: 0.13
Nodes (23): Inventory, ProductNotFoundError, Resolve free-text to product_id: catalog code, barcode, or name., resolve_product_id(), resolve_product(), safe_resolve(), load_inventory(), load_replenishment_params() (+15 more)

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

### Community 85 - "prompt_compiler.py"
Cohesion: 0.23
Nodes (14): InteractionEvent, compile_analyze_prompt(), _dashboard_summary(), _delta_vs_root(), _event_line(), prompt_hash(), _purchase_top(), PanelMode (+6 more)

### Community 86 - "models.py"
Cohesion: 0.24
Nodes (12): CategoryBar, CategorySalesBar, ChatRequest, CoverageBar, ProductContext, ProductSearchHit, ResolutionResult, SalesHistory (+4 more)

### Community 87 - "Tasks: natural-query-interpretation"
Cohesion: 0.25
Nodes (7): Phase 0 — SDD, Phase 1 — Un grupo + scope en chat (MVP), Phase 2 — Multi-grupo comparativo, Phase 3 — inventory_risk sobre grupos, Phase 4 — Desambiguación, Tasks: natural-query-interpretation, Verify

### Community 88 - "config.py"
Cohesion: 0.27
Nodes (9): effective_analyze_rate_limit(), effective_chat_rate_limit(), is_test_env(), ChatRateLimitMiddleware, BaseHTTPMiddleware, Request, Response, Rate limit POST /chat and POST /replenishment/analyze by client IP. (+1 more)

### Community 89 - "InventoryDashboard"
Cohesion: 0.35
Nodes (10): InventoryDashboard, SuggestedFilter, Deterministic suggested filter chips from slice data (no LLM)., suggest_next_filters(), Tests for deterministic suggested filter chips., _snap(), test_suggest_at_most_three(), test_suggest_open_sku_from_top_item() (+2 more)

### Community 90 - "Proposal: natural-query-interpretation"
Cohesion: 0.33
Nodes (5): Non-Goals, Proposal: natural-query-interpretation, Success Criteria, What Changes, Why

### Community 91 - "safe_errors.py"
Cohesion: 0.29
Nodes (6): is_production(), BaseHTTPMiddleware, Request, Response, Catch unhandled errors; hide details in production., SafeErrorMiddleware

### Community 92 - "get_replenishment_recommendation"
Cohesion: 0.29
Nodes (8): get_master(), get_replenishment_recommendation(), test_formula_parity(), test_get_master(), test_replenishment_unknown(), asyncio, test_regression_chat_qty_from_calculation_not_llm_text(), test_catalog_service_recommendation_matches_formula()

### Community 93 - "test_analyze_api.py"
Cohesion: 0.36
Nodes (7): _commit_payload(), _insight_payload(), test_analyze_commit_requires_frozen_scope(), test_analyze_commit_with_frozen_scope(), test_analyze_explore_returns_200(), test_analyze_invalid_llm_json_fallback(), test_analyze_rate_limit_429()

### Community 94 - "SecurityHeadersMiddleware"
Cohesion: 0.29
Nodes (5): BaseHTTPMiddleware, Request, Response, Security response headers., SecurityHeadersMiddleware

### Community 95 - "Verify report — interactive-drilldown"
Cohesion: 0.33
Nodes (6): Spec coverage, TDD cycle evidence, Traceability, UX checklist (5 min manual), Verdict, Verify report — interactive-drilldown

### Community 96 - "Verify: natural-query-interpretation"
Cohesion: 0.33
Nodes (5): API checks, Manual smoke (recommended), Non-goals confirmed, pytest, Verify: natural-query-interpretation

### Community 97 - "SupplyContext"
Cohesion: 0.47
Nodes (5): ReplenishmentParams, SaleRecord, SupplyContext, _seed_context_for_high_qty(), test_run_supplymate_zero_quantity_triangulation()

### Community 98 - "test_api_contract.py"
Cohesion: 0.40
Nodes (3): _minimal_chat_explore(), test_contract_analyze_response_schema(), test_contract_chat_response_schema()

## Knowledge Gaps
- **316 isolated node(s):** `C:\Users\Equipo\.local\bin\graphify.exe`, `MetricContract`, `supplymate`, `smoke_api.sh script`, `Project conventions` (+311 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 510 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AnalyticalScope` connect `AnalyticalScope` to `dashboard.py`, `run_supplymate`, `agent.py`, `test_api_contract.py`, `catalog_service.py`, `streamlit_app.py`, `test_guidance_plan.py`, `api.py`, `prompt_compiler.py`, `models.py`, `InventoryDashboard`, `test_analyze_api.py`?**
  _High betweenness centrality (0.094) - this node is a cross-community bridge._
- **Why does `run_supplymate()` connect `run_supplymate` to `SupplyContext`, `agent.py`, `AnalyticalScope`, `products.py`, `test_guidance_plan.py`, `reference_resolver.py`, `api.py`, `ProductNotFoundError`, `get_replenishment_recommendation`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Why does `classify_intent()` connect `agent.py` to `products.py`, `run_supplymate`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Are the 58 inferred relationships involving `AnalyticalScope` (e.g. with `_labels_from_scope()` and `run_apply_chip()`) actually correct?**
  _`AnalyticalScope` has 58 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `run_supplymate()` (e.g. with `ChatResponse` and `GuidanceChip`) actually correct?**
  _`run_supplymate()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `C:\Users\Equipo\.local\bin\graphify.exe`, `MetricContract`, `supplymate` to the rest of the system?**
  _316 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `agent.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05297334244702666 - nodes in this community are weakly interconnected._